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
        cid = $(this).closest('.comment').attr('id').slice(1),
        comments_box = $('#comment-list'+cid);

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
            comments_box.append(comment);
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
    }, ".comments-list .comment")

    // SUBMIT COMMENT
    $(".container").on("submit", ".comment-form", post_comment);
    $(".container").on("click", ".comment .answers", function(e){
        cid = $(this).closest('.comment').attr('id').slice(1)
        // Show the form to answer a comment
        $('#comment-form'+cid).removeClass('hidden').addClass('in');
        $('#comment-list'+cid).removeClass('hidden').addClass('in').focus();
        e.preventDefault();
    });
});
