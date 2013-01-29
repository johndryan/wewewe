// Wrap this function in a closure so we don't pollute the namespace
(function worker() {
	$.ajax({
		url: '/critical_mass_reached',
		success: function(data) {
			dataElements = data.split(",");
			percent = dataElements[0];
			num_users = dataElements[1];
			$('.bar')
				.css("width", percent + "%");
			$('.modal-body .alert span')
				.html(num_users);
			if (percent == '100') {
				$('h1')
					.html("Site Unlocked");
				$('.modal-body .alert strong')
					.html("Status: Unlocked.");
				$('.modal-body .alert')
					.addClass('alert-success');
				$('h1')
					.attr('class', 'unlocked');
				$('.progress')
					.removeClass('progress-striped active');
			} else {
				$('h1')
					.html("Site Locked");
				$('.modal-body .alert strong')
					.html("Status: Locked.");
				$('.modal-body .alert')
					.removeClass('alert-success');
				$('h1')
					.attr('class', 'locked');
				$('.progress')
					.addClass('progress-striped active');
			}
		},
		complete: function() {
			// Schedule the next request when the current one's complete
			setTimeout(worker, 3000);
		}
	});
})();
