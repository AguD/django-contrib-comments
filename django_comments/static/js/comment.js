function replace_breaklines(str){
    return String(str).replace(/\n/g,"<br />");
};

function enter_key(evt){
    //evt.stopPropagation();  Added to make div clickable
    if (evt.which == 13 && !evt.shiftKey){
        $(this).parent().submit();
        evt.preventDefault();
    };
};

function post_comment(e){
    var form = $(this),
        comment_field = form.find("#id_comment"),
        comment = comment_field.val(),
        subButton = form.find(':input[type="submit"]'),
        comments_list = form.closest('.comments-box').children('.comments-list');
    // Check to see if this is a form for a comment instead of other objects
    e.preventDefault();
    comment = replace_breaklines(comment);
    if (!comment) return false;
    //Submit comment
    if (form.data('submitting')){return false} 
    form.data('submitting', true);
    subButton.button('loading');
    $.post(form.attr("action"), form.serializeArray(), function (response){
        if (response.invalid){
            $(".alert").alert('close') //Close any other alerts
            form.before($(response.error_html));            
            focusError();
        } else if (response.success) {
            comment = $(response.comment_html);
            comments_list.append(comment);
            comment.fadeIn("slow", function() {
                comment.addClass('in');
            });
            //scrollToElement(".comments-wrapper");
        }
        form.data('submitting', false);
        subButton.button('reset')
    }, "json");
    // Clears the input field
    comment_field.val('')
}
// $(document).on("keypress",".comentario", enter_key);

$(document).ready(function() {
    $(".container").on({
        mouseenter: function(e) {
            $(this).find(".vote_buttons:first").addClass("in");
            e.stopPropagation();
        }, mouseleave: function(e) {
            // We dont stop propagation here! Mouseenter the parent, 
            //mouseenter the child, mouseleave it, and we miss the parent's mouseleave
            $(this).find(".vote_buttons:first").removeClass("in");
        }
    }, ".comments-list .comment");

    // SUBMIT COMMENT
    $(".container").on("submit", ".comment-form form", post_comment);
    $(".container").on("click", ".comment .answers", function(e){
        e.preventDefault();
        var cid = $(this).closest('.comment').attr('id').slice(1);
        var current_box = $('#comment-box'+cid);
        var parents_boxes = $(this).parents('.comments-box');
        // Exclude parents comments boxes and current element
        var exclude = $.merge($.merge([], parents_boxes), current_box);
        // Hide displayed boxes except for parents (they hold this box)
        $('.comments-box').not(exclude)
            .removeClass('in')
            .addClass('hidden');
        // Show current box
        current_box.children('.comment-form').removeClass('hidden')
        current_box
            .removeClass('hidden')
            .one($.support.transition.end, function(){
                current_box.addClass('in');                
            })
            .emulateTransitionEnd(200);
        // In parents boxes only hide forms, except main parent.
        parents_boxes.not('.main').children('.comment-form').addClass('hidden');
    });
});
