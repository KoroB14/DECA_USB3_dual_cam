`timescale 1ns / 1ps
`default_nettype none
//////////////////////////////////////////////////////////////////////////////////
// Dmitry Koroteev
// korob14@gmail.com
//////////////////////////////////////////////////////////////////////////////////
//
// 
// | reg settings              | COLOR_MODE | FPGA_PROCESSING |               Comment                     |
// | OV5642_1280p_30f_rgb.mif  |     2      |        2        | 1280 x 720 x 30 FPS RGB565                |
// | OV5642_1280p_60f_gray.mif |     1      |        2        | 1280 x 720 x 60 FPS GRAY8 Cam processing  |
// | OV5642_1920p_15f_rgb.mif  |     2      |        2        | 1920 x 1080 x 15 FPS RGB565               |
// | OV5642_1920p_30f_gray.mif |     1      |        2        | 1920 x 1080 x 30 FPS GRAY8 Cam processing |
module deca_usb3_dual_cam
#(	parameter IM_X = 1920,
	parameter IM_Y = 1080,
	parameter COLOR_MODE = 1,		// 1 - Grayscale, 2 - RGB565
	parameter FPGA_PROCESSING = 2,// 1 - Convert RGB565 -> 8-bit Grayscale, 2 - No processing
	parameter CAMERA_ADDR = 8'h78,// 8'h60 - OV2640, 8'h42 - OV7670, 8'h78 - OV5642
	parameter MIF_FILE = "./rtl/cam_config/OV5642_1920p_30f_gray.mif", // Camera registers init file
	parameter FAST_SIM = 0			// 1- Fast simulation mode, skip camera initialization
)
(
	//System
	input wire						clk_50,
	input wire						rst_n,
	
	//CYUSB 3014
	input wire 						USB_CLK,
	inout	tri			[15:0]	DQ,
	output wire						RD,
	output wire						WR,
	output wire						LastWRData,
	output wire						OE,
	output wire			[1:0]		DMA0_Address, 
	input wire						DMA0_Ready,
	input wire						DMA0_Watermark,
	input wire						DMA1_Ready,
	input wire						DMA1_Watermark,
		
	//Cam_R DVP 
	input	wire			[7:0]		data_cam_r,
	input wire						VSYNC_cam_r,
	input wire						HREF_cam_r,
	input wire						PCLK_cam_r,	
	output wire						XCLK_cam_r,
	output wire						res_cam_r,
	output wire						on_off_cam_r,	
		
	//Cam_L DVP 
	input	wire			[7:0]		data_cam_l,
	input wire						VSYNC_cam_l,
	input wire						HREF_cam_l,
	input wire						PCLK_cam_l,	
	output wire						XCLK_cam_l,
	output wire						res_cam_l,
	output wire						on_off_cam_l,
	
	//Cam R&L SCCB
	output wire						sioc,
	output wire						siod
	
	
);
//declarations
wire 			rst_s;
wire			conf_done;

//Cam intefaces
Cam_If		Cam_R_IF(
	.data_cam(data_cam_r),
	.VSYNC_cam(VSYNC_cam_r),
	.HREF_cam(HREF_cam_r),
	.PCLK_cam(PCLK_cam_r),
	.on_off_cam(on_off_cam_r),
	.conf_done(conf_done)
);

Cam_If		Cam_L_IF(
	.data_cam(data_cam_l),
	.VSYNC_cam(VSYNC_cam_l),
	.HREF_cam(HREF_cam_l),
	.PCLK_cam(PCLK_cam_l),
	.on_off_cam(on_off_cam_l),
	.conf_done(conf_done)
);

//OV5642 assignments
assign res_cam_r = 0;
assign XCLK_cam_r = 1'bz;

assign res_cam_l = 0;
assign XCLK_cam_l = 1'bz;

//rst sync
sync rst_sync
(
	.in					(rst_n),
	.clk					(clk_50),
	.out					(rst_s)
);

//camera config
camera_configure 
#(	
    .CLK_FREQ			(50000000),
	 .CAMERA_ADDR		(CAMERA_ADDR),
	 .MIF_FILE			(MIF_FILE),
	 .I2C_ADDR_16		(1'b1),
	 .FAST_SIM			(FAST_SIM)
)
camera_configure_0
(
    .clk					(clk_50),	
	 .rst_n				(rst_s),
	 .sioc				(sioc),
    .siod				(siod),
	 .done				(conf_done)
	
);

//cam capture r
cam_capture 
#(
	.COLOR_MODE			(FPGA_PROCESSING),
	.IM_X					(IM_X),
	.IM_Y					(IM_Y)
)
cam_capture_r
(
	.rst_n				(rst_s),
	.IF					(Cam_R_IF.Camera)

);

//cam capture l
cam_capture 
#(
	.COLOR_MODE			(FPGA_PROCESSING),
	.IM_X					(IM_X),
	.IM_Y					(IM_Y)
)
cam_capture_l
(
	.rst_n				(rst_s),
	.IF					(Cam_L_IF.Camera)

);

//Main control
MainFSM
# (
	.IM_X					(IM_X),
	.IM_Y					(IM_Y),
	.COLOR_MODE			(COLOR_MODE)
	)
MainFSM_Inst
(
    .USB_CLK			(USB_CLK),
	 .rst_n				(rst_s),
    .WR					(WR), 
	 .RD					(RD),
	 .LastWRData		(LastWRData),
	 .OE					(OE),
	 .DMA0_Address		(DMA0_Address),
	 .DMA0_Ready		(DMA0_Ready),
	 .DMA0_Watermark	(DMA0_Watermark),
	 .DMA1_Ready		(DMA1_Ready), 
	 .DMA1_Watermark	(DMA1_Watermark), 
	 .DQ					(DQ),
	 .Cam_R_IF			(Cam_R_IF.Cons),
	 .Cam_L_IF			(Cam_L_IF.Cons)
	 	 
);

endmodule
