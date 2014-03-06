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

$(function(){

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

    $('#update-form').on('submit', function(e) {
        e.preventDefault();
        var $form = $(this);
        $.ajax({
            url: $form.attr('action'),
            data: $form.serialize(),
            type: 'POST'
        }).done(function(data, status, req) {
            window.location = '/';
        }).fail(function(req, status, error) {
            alert('Couldn\'t update link: ' + error);
        });
    });

    $('#delete-form').on('submit', function(e) {
        e.preventDefault();
        if(confirm('Are you sure you want to permanently delete this link?')) {
            var $form = $(this);
            $.ajax({
                url: $form.attr('action'),
                type: 'DELETE'
            }).done(function(data, status, req) {
                window.location = '/';
            }).fail(function(req, status, error) {
                alert('Couldn\'t delete link: ' + error);
            });
        }
    });

    $('#header-search').on('submit', function(e) {
        if($('#q').val() === '')
            e.preventDefault();
    });

});