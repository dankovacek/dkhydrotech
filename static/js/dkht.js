$( document ).ready(function() {
    console.log("Document ready.");

    $('.sidenav').sidenav();
    $('.parallax').parallax();

});

var lastScrollTop = 0;

$(document).on("scroll", function(){
    var currScrollTop = $(this).scrollTop();
    if (currScrollTop > lastScrollTop){
        $("nav").addClass("shrink");
        $("nav-wrapper").addClass("shrink");
    }
    else {
        $("nav").removeClass("shrink");
        $("nav-wrapper").removeClass("shrink");
    }
    lastScrollTop = currScrollTop;
});


// $( window ).on("load", function() {
//     $('.grid').masonry({
//         itemSelector: '.grid-item',
//         percentPosition: true,
//         columnWidth: '.grid-sizer',
//         horizontalOrder: true,
//     });
// });
