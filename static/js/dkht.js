$(document).ready(function () {
  console.log("Document ready.");
  $(".dropdown-button").dropdown({
    hover: false,
    constrainWidth: false
  });
  $('.parallax').parallax();
  $(".button-collapse").sideNav();
  $('select').material_select();

});

// document.addEventListener('DOMContentLoaded', function () {
//   var elems = document.querySelectorAll('.tooltipped');
//   var instances = M.Tooltip.init(elems, options);
// });
