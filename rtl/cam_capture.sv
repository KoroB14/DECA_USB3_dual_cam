//////////////////////////////////////////////////////////////////////////////////
// Dmitry Koroteev
// korob14@gmail.com
//////////////////////////////////////////////////////////////////////////////////
`timescale 1 ns / 1 ps

module cam_capture
#(	parameter COLOR_MODE = 1,
	parameter IM_X = 1280,
	parameter IM_Y = 720
)
(         
	input wire 					rst_n,
	Cam_If.Camera 				IF
	
);


reg 						second_byte;	
reg 						pixdata_valid;
reg 						RGB_valid;
reg						pixel_valid_r;
reg						start;
reg 		[15:0] 		pixdata;	
reg 		[7: 0] 		R, G, B;
reg 		[7: 0]		pixel_r;
wire 						vsync_fall;
wire 						start_stream_s;
wire 						rst_n_cam;

assign 					IF.on_off_cam = IF.conf_done && !IF.start_stream;
assign					rst_n_cam = rst_n && IF.conf_done;

//Vsync falling edge detector
detect_falling_edge detect_vsync_fedge
(
	.clk(IF.PCLK_cam),
	.rst_n(rst_n_cam),
	.signal(IF.VSYNC_cam),
	.out(vsync_fall)
);

//sync start stream
sync st_stream_sync
(
	.in(IF.start_stream),
	.clk(IF.PCLK_cam),
	.out(start_stream_s)
);

// Start signal
always @ (posedge IF.PCLK_cam or negedge rst_n_cam)
	if (!rst_n_cam)
		start <= 0;
	else if (vsync_fall & IF.out_ready & start_stream_s)
		start <= 1'b1;
	else if (!start_stream_s)
		start <= 0;

//Generate pipeline or reg
generate

if (COLOR_MODE == 1) begin: Generate_Grayscale		
always @( posedge IF.PCLK_cam or negedge rst_n_cam )
		if (!rst_n_cam)
			second_byte		<= 1'h0;
		else
			if (IF.HREF_cam & start)
				second_byte	<= ~second_byte;
			else
				second_byte	<= 1'h0;	
//Capture two bytes			
always @( posedge IF.PCLK_cam or negedge rst_n_cam )
	if (!rst_n_cam) begin
		pixdata	<= 0;
		pixdata_valid <= 0;
		end
	else if (start)
		if (second_byte) begin
				pixdata[7:0]  <= IF.data_cam;
				pixdata_valid <= 1'b1;
				end
		else begin
				pixdata[15:8] <= IF.data_cam;
				pixdata_valid <= 0;
				end
	else 
		pixdata_valid <= 0;
//Convert to RGB888	
always @ (posedge IF.PCLK_cam)
if (!pixdata_valid) begin
	R	<= 0;
	G	<= 0;
	B	<= 0;
	RGB_valid <= 0;
	end
else begin
	R	<= {pixdata[ 15: 11], pixdata[15:13]};
	G	<= {pixdata[10: 5], pixdata[10:9]};
	B	<= {pixdata[ 4: 0], pixdata[4:2]};
	RGB_valid <= 1'b1;
	end
//Convert to grayscale
always @( posedge IF.PCLK_cam)
if (!RGB_valid) begin
	pixel_r <= 0;
	pixel_valid_r <= 0;
	end
else begin
	pixel_r <= (R>>2)+(R>>5)+(G>>1)+(G>>4)+(B>>4)+(B>>5);
	pixel_valid_r <= IF.out_ready;
	end	

end
// Reg for RGB
else if (COLOR_MODE == 2) begin: Generate_RGB
always @( posedge IF.PCLK_cam or negedge rst_n_cam )
	if (!rst_n_cam) begin
		pixel_r <= 0;
		pixel_valid_r <= 0;
		end
	else begin
		pixel_r <= IF.data_cam;
		pixel_valid_r <= IF.HREF_cam & start & IF.out_ready;
		end


end

endgenerate

assign IF.pixel = pixel_r;
assign IF.pixel_valid = pixel_valid_r;
	

endmodule


