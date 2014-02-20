// Saves options to localStorage.
function save_options() {
    var postUrl = document.getElementById('post_url').value;
    localStorage['post_url'] = postUrl;
    // Update status to let user know options were saved.
    var status = document.getElementById('status');
    status.innerHTML = 'Options Saved.';
    setTimeout(function() {
        status.innerHTML = '';
    }, 750);
}

// Restores select box state to saved value from localStorage.
function restore_options() {
    var postUrl = localStorage['post_url'];
    if (!postUrl) {
        return;
    }
    document.getElementById('post_url').value = postUrl;
}

document.addEventListener('DOMContentLoaded', restore_options);
document.querySelector('#save').addEventListener('click', save_options);