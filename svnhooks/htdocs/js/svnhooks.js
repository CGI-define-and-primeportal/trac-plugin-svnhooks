(function($){
  $(document).ready(function(e){
    $('.moreinfo,.lessinfo').click(function(e) {
            $("i", this).toggleClass('icon-resize-full icon-resize-small')
            $(this).closest('tr').next().toggleClass('hidden');
            return false;
     });
     
     $('.showoption,.hideoption').click(function(e) {
       $("i", this).toggleClass('icon-resize-full icon-resize-small')
       $(this).closest('thead').next().toggleClass('hidden');
       return false;
     });
     
     $(".selcheckbox").click(function() {
     	$(".remove-button").enable(false);
     	$(".selcheckbox").each(function() {
     		if(this.checked) {$(".remove-button").enable(true); return false;}
        	});
     });
     
     $('#add').click(function(e) {
	 if($("#hook").val() ==0) {
	   $("#hook").addClass("ui-state-error");
	   $("#hook").after('<span class="hook_required">This field is required.</span>');
	 } else if($("#path").val() =='') {
	 	$("#path").addClass("ui-state-error");
	   	$("#path").after('<span class="path_required">This field is required.</span>');
	 } else {
	  $("#hook", "#path").removeClass("ui-state-error");
	  return true;
	 }
	 
	 return false;
     });

  });
  

})(jQuery)
