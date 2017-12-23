$( document ).ready(function() {
    console.log("Document ready.");
    $(".dropdown-button").dropdown( {
      hover: false,
      constrainWidth: false
    } );
    $('.parallax').parallax();
    $(".button-collapse").sideNav();

});
