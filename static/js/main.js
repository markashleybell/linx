$(function(){

    // Instantiate the Bloodhound suggestion engine
    var tags = new Bloodhound({
        // Each tag item returned by the /tags endpoint has a tokens property
        // containing all the unique susbtrings of that tag, so just use it directly
        datumTokenizer: function(d) { return d.tokens; },
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        prefetch: {
            // Currently this just reloads all tags on every page refresh
            thumbprint: new Date().getTime(),
            url: '/tags',
            filter: function(data) {
                return data.tags;
            }
        }
    });

    tags.initialize();

    $('#q, #tags').tagInput({
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

    $('#results a[rel="external"]').attr('target', '_blank');

    $('li.disabled a').on('click', function(e) { e.preventDefault(); });

});