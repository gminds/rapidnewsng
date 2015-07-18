jQuery(document).ready(function($) 
    {
	$(".vote_form").submit(function(e) 
		{
		    e.preventDefault(); 
		    var btn = $("button", this);
		    var l_id = $(".hidden_id", this).val();
		    btn.attr('disabled', true);
		    $.get("/vote/", $(this).serializeArray(),
			  function(data) {
			      if(data["voteobj"]) {
				  btn.text("Dislike");
			      }
			      else {
				  btn.text("Like");
			      }
			  });
		    btn.attr('disabled', false);
		});
    });