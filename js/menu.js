$(function() {
    $(document).contextMenu({
        menu: 'context-menu'
    },
    function(action, el, pos) {
        window.location = '#' + action;
    });
});
