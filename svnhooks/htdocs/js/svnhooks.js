(function($){
  $(document).ready(function(e){
    $('.moreinfo,.lessinfo').click(function(e) {
            $(this).toggleClass('moreinfo lessinfo')
            $(this).closest('tr').next().toggleClass('hidden');
            return false;
     });
     
     $('.showoption,.hideoption').click(function(e) {
                 $(this).toggleClass('showoption hideoption')
                 $(this).closest('tbody').next().toggleClass('hidden');
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
