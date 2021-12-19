interface Cam_If (input 		PCLK_cam,
						input 		HREF_cam,
						input 		VSYNC_cam,
						input			conf_done,
						output		on_off_cam,
						input [7:0] data_cam);
	
	logic 				out_ready;
	logic					start_stream;
	logic 	[7:0]		pixel;
	logic					pixel_valid;
	
	modport Camera (
	input data_cam, VSYNC_cam, HREF_cam, PCLK_cam, out_ready, start_stream, conf_done,
	output pixel, pixel_valid, on_off_cam
	);
	
	modport Cons (
	input pixel, pixel_valid, PCLK_cam,
	output out_ready, start_stream
	);
endinterface
