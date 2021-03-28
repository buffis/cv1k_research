`define U2_HIGH_BITS 2'b00
`define AUDIO_HIGH_BITS 2'b01
`define EEPROM_HIGH_BITS 2'b11

`define EEPROM_LOW_BITS 2'b01
`define SETUP_LOW_BITS 2'b10
`define U2_CS_LOW_BITS 2'b11

module cv1k(
	input reset,
	input clock,                 // From SH-3
	input clock2,                // From FPGA
	input cs4,                   // U2, EEPROM/RTC, Audio, Initialize commands
	input cs5,                   // Unused.
	input cs6,                   // Blitter
	input sh3_rd,                // Memory read from SH-3
	input sh3_we,                // Memory write from SH-3
	output sh3_wait,             // Hardware wait signal. Seems unused
	output reg u2_ce,            // Enables U2 when low
	output reg u2_re,            // Read from U2 when low
	output reg u2_we,            // Write to U2 when low
	input eeprom_do,             // Data from EEPROM/RTC
	input eeprom_tirq,           // Unused.
	output reg eeprom_di,        // Data to EEPROM/RTC
	output reg eeprom_clock,     // Clock for EEPROM/RTC serial transfer
	output reg eeprom_ce,        // High when EEPROM/RTC is in use
	output reg eeprom_foe,       // Low except during setup
	input audio_play,            // Unused.
	output reg audio_cs,         // Low when communicating with audio IC
	output audio_reset,          // High except during setup
	output blitter_out,          // Low on write to blitter
	output global_clr,           // Global clear. Always low.
	output reg eeprom_is_output, // High when reading data from EEPROM/RTC
	input global_oe,             // Global output enable. Tied externally to eprom_is_output
	inout [3:0]data,             // Data bus
	input [1:0]addr_high,        // A23, A22
	input [1:0]addr_low,         // A1,  A0
	input a2                     // Unused.
	);
	
	// Handle state setup.
	// Just wait until we get "1110" on the data bus at address 0x10C00002
	// which triggers after FPGA setup. Consider things initialized then.
	reg device_ready;
  	always @(posedge clock, negedge reset) begin
		if (!reset) device_ready <= 1'b0;
		else if (!cs4 && addr_high == `EEPROM_HIGH_BITS && addr_low == `SETUP_LOW_BITS && data == 4'b1110) begin
			device_ready <= 1'b1;
		end
	end
	
	// Audio reset seems to be the main thing I've verified that actually changes after the "1110" 
	// command to 0x10C00002.
	assign audio_reset = device_ready;
	
	// SH3 Wait seems unused (always high).
	assign sh3_wait = 1'b1;
	
	// Global clear seems always low.
	assign global_clr = 1'b0;
	
	// Blitter out is tied directly to CS6.
	assign blitter_out = cs6;
	
	// The only time the CPLD data bus is used for output is during reads from the EEPROM/RTC.
	// Otherwise it's used as input.
	// Note that "eeprom_is_output" and "global_oe" are connected externally on the PCB.
	reg [3:0]eeprom_data_out = 4'b1110;
	assign data = global_oe ? eeprom_data_out : 4'bZ;
  
	// The signals in this block does not appear to be clocked.
	// Audio, U2 and EEPROM/RTC are both handled through CS4, but use A23-A22 for addressing.
	//
	// Audio CS is just mapped to any access to its memory range A23=0,A22=1.
	//
	// U2 RE/WE are trigered by the RD and WE signals from the SH3 when accessing its memory
	// range A23=0,A22=0. There's an assumption that both RD and WE are not low at once.
	//
	// EEPROM/RTC being used as output is signaled through sh3_rd pulsing low and accessing
	// A23=1,A22=1. Technically it would be good to also check sh3_we for writes, but doesn't
	// seem needed. This address range is also used for some other commands, but none of that
	// affects the output calculation.
	always @(sh3_rd, sh3_we, cs4, addr_high) begin
		case (addr_high)
			`AUDIO_HIGH_BITS: begin
				audio_cs = cs4;
				u2_re = 1'b1;
				u2_we = 1'b1;
				eeprom_is_output = 1'b0;
			end
			`U2_HIGH_BITS: begin	
				audio_cs = 1'b1;
				u2_re = sh3_rd | cs4;
				u2_we = sh3_we | cs4;
				eeprom_is_output = 1'b0;
			end
			`EEPROM_HIGH_BITS: begin
				audio_cs = 1'b1;
				u2_re = 1'b1;
				u2_we = 1'b1;
				eeprom_is_output = !(sh3_rd | cs4);
			end
			default: begin // Don't enable anything.
				audio_cs = 1'b1;
				u2_re = 1'b1;
				u2_we = 1'b1;
				eeprom_is_output = 1'b0;
			end
		endcase
	end
	
	// Only stuff accessing the data bus appears clocked.
	// In addition to the initialize state at the top of this file, this means just EEPROM writes
	// and changes to U2 CE (chip select).
	// Note that the FOE signal for EEPROM/RTC is set low at the first access.
	always @(posedge clock, negedge reset) begin
		if (!reset) begin
			eeprom_di    <= 1'b0;
			eeprom_ce    <= 1'b0;
			eeprom_clock <= 1'b0;
			eeprom_foe   <= 1'b1;
			u2_ce        <= 1'b1;
		end else begin
			eeprom_data_out[0] = eeprom_do;
			if (!cs4 && addr_high == `EEPROM_HIGH_BITS) begin				
				case(addr_low)
					`U2_CS_LOW_BITS: u2_ce <= !data[0];
					`EEPROM_LOW_BITS: begin
						eeprom_foe <= 1'b0;
						if (!sh3_we) begin
							eeprom_ce    <= data[2];
							eeprom_clock <= data[1];
							eeprom_di    <= data[0];
						end
					end
				endcase
			end
		end
	end
endmodule

