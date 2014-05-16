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
        comment_field = $("#id_comment")
        comment = comment_field.val(),
        subButton = form.find(':input[type="submit"]'),
        comments_box = $(".comments-wrapper");

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
            comment.addClass('in');
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
    var comment_input = $("#id_comment");

    $(".comments-wrapper").on({
        mouseenter: function() {
            $(this).find(".vote_buttons").addClass("in");
        }, mouseleave: function() {
            $(this).find(".vote_buttons").removeClass("in");
        }
    }, ".comment")

    // SUBMIT COMMENT
    $("#comment-form").on("submit", post_comment);
});
