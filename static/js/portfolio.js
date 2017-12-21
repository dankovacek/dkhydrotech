$( document ).ready(function() {
    console.log("Document ready.");


    $('select').material_select();

    $(".button-collapse").sideNav({
        menuWidth: 300, // Default is 300
        edge: 'right', // Choose the horizontal origin
        closeOnClick: true, // Closes side-nav on <a> clicks, useful for Angular/Meteor
        draggable: true, // Choose whether you can drag to open on touch screens,
        onOpen: function(el) { /* Do Stuff */ }, // A function to be called when sideNav is opened
        onClose: function(el) {/* Do Stuff */ }, // A function to be called when sideNav is closed
    });

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


$( window ).on("load", function() {
    $('.grid').masonry({
        itemSelector: '.grid-item',
        percentPosition: true,
        columnWidth: '.grid-sizer',
        horizontalOrder: true,
    });
});

$('.button-collapse').sideNav({

    }
);

