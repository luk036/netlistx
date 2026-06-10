module fir_filter #(
    parameter DATA_WIDTH = 16,
    parameter COEF_WIDTH = 16,
    parameter ACC_WIDTH = 32,
    parameter TAPS = 32
)(
    input clk,
    input rst_n,
    input [DATA_WIDTH-1:0] data_in,
    output reg [DATA_WIDTH-1:0] data_out,
    output reg valid_out
);

    reg signed [DATA_WIDTH-1:0] shift_reg [0:31];
    reg signed [ACC_WIDTH-1:0] accumulator;
    reg [4:0] tap_counter;
    reg processing;

    wire signed [COEF_WIDTH-1:0] coefficients [0:31];
    assign coefficients[0] = 16'sd415;
    assign coefficients[1] = 16'sd1251;
    assign coefficients[2] = 16'sd2017;
    assign coefficients[3] = 16'sd2876;
    assign coefficients[4] = 16'sd3725;
    assign coefficients[5] = 16'sd4428;
    assign coefficients[6] = 16'sd4858;
    assign coefficients[7] = 16'sd4957;
    assign coefficients[8] = 16'sd4615;
    assign coefficients[9] = 16'sd3904;
    assign coefficients[10] = 16'sd2872;
    assign coefficients[11] = 16'sd1671;
    assign coefficients[12] = 16'sd471;
    assign coefficients[13] = -16'sd557;
    assign coefficients[14] = -16'sd1307;
    assign coefficients[15] = -16'sd1694;
    assign coefficients[16] = -16'sd1697;
    assign coefficients[17] = -16'sd1374;
    assign coefficients[18] = -16'sd842;
    assign coefficients[19] = -16'sd245;
    assign coefficients[20] = 16'sd298;
    assign coefficients[21] = 16'sd702;
    assign coefficients[22] = 16'sd900;
    assign coefficients[23] = 16'sd876;
    assign coefficients[24] = 16'sd708;
    assign coefficients[25] = 16'sd405;
    assign coefficients[26] = 16'sd110;
    assign coefficients[27] = -16'sd144;
    assign coefficients[28] = -16'sd317;
    assign coefficients[29] = -16'sd382;
    assign coefficients[30] = -16'sd369;
    assign coefficients[31] = -16'sd454;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            shift_reg[0] <= 0; shift_reg[1] <= 0; shift_reg[2] <= 0;
            shift_reg[3] <= 0; shift_reg[4] <= 0; shift_reg[5] <= 0;
            shift_reg[6] <= 0; shift_reg[7] <= 0; shift_reg[8] <= 0;
            shift_reg[9] <= 0; shift_reg[10] <= 0; shift_reg[11] <= 0;
            shift_reg[12] <= 0; shift_reg[13] <= 0; shift_reg[14] <= 0;
            shift_reg[15] <= 0; shift_reg[16] <= 0; shift_reg[17] <= 0;
            shift_reg[18] <= 0; shift_reg[19] <= 0; shift_reg[20] <= 0;
            shift_reg[21] <= 0; shift_reg[22] <= 0; shift_reg[23] <= 0;
            shift_reg[24] <= 0; shift_reg[25] <= 0; shift_reg[26] <= 0;
            shift_reg[27] <= 0; shift_reg[28] <= 0; shift_reg[29] <= 0;
            shift_reg[30] <= 0; shift_reg[31] <= 0;
            tap_counter <= 0;
            processing <= 0;
            accumulator <= 0;
            valid_out <= 0;
        end else begin
            shift_reg[0] <= data_in;
            shift_reg[1] <= shift_reg[0];
            shift_reg[2] <= shift_reg[1];
            shift_reg[3] <= shift_reg[2];
            shift_reg[4] <= shift_reg[3];
            shift_reg[5] <= shift_reg[4];
            shift_reg[6] <= shift_reg[5];
            shift_reg[7] <= shift_reg[6];
            shift_reg[8] <= shift_reg[7];
            shift_reg[9] <= shift_reg[8];
            shift_reg[10] <= shift_reg[9];
            shift_reg[11] <= shift_reg[10];
            shift_reg[12] <= shift_reg[11];
            shift_reg[13] <= shift_reg[12];
            shift_reg[14] <= shift_reg[13];
            shift_reg[15] <= shift_reg[14];
            shift_reg[16] <= shift_reg[15];
            shift_reg[17] <= shift_reg[16];
            shift_reg[18] <= shift_reg[17];
            shift_reg[19] <= shift_reg[18];
            shift_reg[20] <= shift_reg[19];
            shift_reg[21] <= shift_reg[20];
            shift_reg[22] <= shift_reg[21];
            shift_reg[23] <= shift_reg[22];
            shift_reg[24] <= shift_reg[23];
            shift_reg[25] <= shift_reg[24];
            shift_reg[26] <= shift_reg[25];
            shift_reg[27] <= shift_reg[26];
            shift_reg[28] <= shift_reg[27];
            shift_reg[29] <= shift_reg[28];
            shift_reg[30] <= shift_reg[29];
            shift_reg[31] <= shift_reg[30];

            if (!processing) begin
                tap_counter <= 0;
                accumulator <= 0;
                processing <= 1;
            end else if (tap_counter < 32) begin
                accumulator <= accumulator + (shift_reg[tap_counter] * coefficients[tap_counter]);
                tap_counter <= tap_counter + 1;
            end else begin
                data_out <= accumulator[31:16];
                valid_out <= 1;
                processing <= 0;
            end
        end
    end

endmodule
