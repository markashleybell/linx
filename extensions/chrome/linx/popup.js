// This callback function is called when the content script has been 
// injected and returned its results
function onPageDetailsReceived(pageDetails)  { 
    document.getElementById('title').value = pageDetails.title; 
    document.getElementById('url').value = pageDetails.url; 
    document.getElementById('abstract').innerText = pageDetails.abstract; 
} 

var result = null;

// POST the data to the server using XMLHttpRequest
function addBookmark(event) {

    // Cancel the form submit
    event.preventDefault();

    // Get the REST endpoint URL from the extension config
    var postUrl = localStorage['post_url'];
    if (!postUrl) {
        alert('POST Url is not set');
        return;
    }

    // Build up an asynchronous AJAX POST request
    var xhr = new XMLHttpRequest();
    xhr.open('POST', postUrl, true);

    // URLEncode each field's contents
    var params = 'link_id=0' + 
                 '&title=' + encodeURIComponent(document.getElementById('title').value) + 
                 '&url=' + encodeURIComponent(document.getElementById('url').value) + 
                 '&abstract=' + encodeURIComponent(document.getElementById('abstract').value) +
                 '&tags=' + encodeURIComponent(document.getElementById('tags').value);
    
    // Replace any instances of the URLEncoded space char with +
    params = params.replace(/%20/g, '+');

    // Set correct header for form data
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    
    // Handle request state change events
    xhr.onreadystatechange = function() { 
        // If the request completed
        if (xhr.readyState == 4) {
            result.removeClass('label-default label-success label-danger');
            // If the request was successful
            if (xhr.status == 200) {
                var json = JSON.parse(xhr.responseText);
                // If an error message was returned, show it
                if(typeof json.error !== 'undefined') {
                    result.html(json.error);
                    result.addClass('label-danger');  
                } else { // If the data was successfully saved
                    result.html('Saved!');
                    result.addClass('label-success');
                    // Close the popup after a short delay
                    window.setTimeout(window.close, 1000);
                }
            } else {// Show what went wrong
                result.html('Error saving: ' + xhr.statusText);
                result.addClass('label-danger');
            }
        }
    };

    // Send the request
    xhr.send(params);

    result.html('Saving...');
    result.removeClass('label-default label-success label-danger');
    result.addClass('label-default');
    result.show();

}

// When the popup HTML has loaded
window.addEventListener('load', function(evt) {

    result = $('#result');

    // Handle the bookmark form submit event with our addBookmark function
    document.getElementById('addbookmark').addEventListener('submit', addBookmark);
    
    // Get the event page
    chrome.runtime.getBackgroundPage(function(eventPage) {
        // Call the getPageInfo function in the event page, passing in our onPageDetailsReceived 
        // function as the callback. This injects content.js into the current tab's HTML
        eventPage.getPageDetails(onPageDetailsReceived);
    });

    var tagJsonUrl = localStorage['tag_json_url'];
    if (!tagJsonUrl) {
        alert('Tag JSON Url is not set');
        return;
    }

    // Instantiate the Bloodhound suggestion engine
    var tags = new Bloodhound({
        // Each tag item returned by the /tags endpoint has a tokens property
        // containing all the unique susbtrings of that tag, so just use it directly
        datumTokenizer: function(d) { return d.tokens; },
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        prefetch: {
            // Currently this just reloads all tags on every page refresh
            thumbprint: new Date().getTime(),
            url: tagJsonUrl,
            filter: function(data) {
                return data.tags;
            }
        }
    });

    tags.initialize();

    $('#tags').tagInput({
        allowDuplicates: false,
        typeahead: true,
        typeaheadOptions: {
            highlight: true
        },
        typeaheadDatasetOptions: {
            displayKey: 'tag',
            source: tags.ttAdapter()
        }
    });
    
});