$(document).ready(function () {
  console.log("Document ready.");
  $(".dropdown-button").dropdown({
    hover: false,
    constrainWidth: false
  });
  $('.parallax').parallax();
  $(".button-collapse").sideNav();
  $('select').material_select();

  console.log("Markdownx ready");

  // $('.markdownx').on('markdownx.init', function() {
  //    console.log("INIT");
  // });
  // $('.markdownx').on('markdownx.update', function(e, response) {
  //    console.log("UPDATE" + response);
  // });

});

document.addEventListener('DOMContentLoaded', function () {
  var elems = document.querySelectorAll('.tooltipped');
  var instances = M.Tooltip.init(elems, options);
});
