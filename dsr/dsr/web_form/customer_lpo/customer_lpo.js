frappe.ready(function() {
	// bind events here

});

frappe.web_form.on('fuel_station', (field, value) => {
	filterFuelItem(fuel_station);
});

function filterFuelItem(fuel_station) {
	$.ajax({
		type: 'GET', 
		url: 'api/resource/Fuel Item?filters=[["Fuel Item","fuel_station","=","${fuel_station}"]]',
		success: function(result) {
			var options = [];
			for (var i = 0; i < result.data.length; i++) {
				options.push({
					'label': result.data[i].name,
					'value': result.data[i].name
				});
			}
			var field = frappe.web_form.field_group.get_field('fuel_item');
			field._data = options;
			field.refresh();
		}
	});
	frappe.msgprint(options)
};	
