$( document ).ready(function() {

    var images = document.getElementsByTagName("img");
    var i;

    for (i=0; i< images.length; i++) {
      images[i].className += "responsive-img";
    }

});
