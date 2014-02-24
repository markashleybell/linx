// This callback function is called when the content script has been 
// injected and returned its results
function onPageInfo(o)  { 
    document.getElementById("title").value = o.title; 
    document.getElementById("url").value = o.url; 
    document.getElementById("abstract").innerText = o.abstract; 
} 

// POST the data to the server using XMLHttpRequest
function addBookmark() {
    var postUrl = localStorage['post_url'];
    if (!postUrl) {
        alert('POST Url is not set');
        return;
    }

    var xhr = new XMLHttpRequest();

    // This async request used to work, but now doesn't for some reason...
    // It works if you 'Inspect popup' and step through the code in the Chrome debugger,
    // but as soon as you close the debugger and try the same thing, the call fails?!??

    // xhr.onreadystatechange = function() { 
    //     // If the request completed, close the extension popup
    //     if (this.readyState == 4) {
    //         if (this.status == 200) 
    //             window.close();
    //     }
    // };

    // xhr.open("POST", postUrl, true);

    // Non-asynchronous request works fine
    xhr.open("POST", postUrl, false);
    
    var params = "link_id=0" + 
                 "&title=" + document.getElementById("title").value + 
                 "&url=" + document.getElementById("url").value + 
                 "&abstract=" + document.getElementById("abstract").value +
                 "&tags=" + document.getElementById("tags").value + 
                 "&xhr=1";
    
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhr.send(params);

    window.close();

    return false;
}

// When the popup HTML has loaded
window.addEventListener("load", function(evt) {
    // Handle the bookmark form submit event with our addBookmark function
    document.getElementById('addbookmark').addEventListener('submit', addBookmark);
    // Call the getPageInfo function in the background page, injecting content_script.js 
    // into the current HTML page and passing in our onPageInfo function as the callback
    chrome.extension.getBackgroundPage().getPageInfo(onPageInfo);

    var tagJsonUrl = localStorage['tag_json_url'];
    if (!tagJsonUrl) {
        alert('Tag JSON Url is not set');
        return;
    }

    // Instantiate the Bloodhound suggestion engine
    var tags = new Bloodhound({
        datumTokenizer: function(d) { return Bloodhound.tokenizers.whitespace(d.tag); },
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        // local: [
        //     { tag: 'tag1' },
        //     { tag: 'tag2' },
        //     { tag: 'tag3' }
        // ]
        prefetch: {
            // Currently this just reloads all tags on every page refresh
            // We'll need to refine this once AJAX updates start happening
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