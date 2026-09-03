module fir_parallel #(
    parameter NUM_TAPS = 167,
    parameter DATA_W = 16,
    parameter COEF_W = 16,
    parameter ACC_W = 40,
    parameter ACC_SHIFT = 17
)
(
    input clk,
    input rst_n,
    input input_valid,
    input wire signed [DATA_W - 1:0] data_in,
    output reg signed [DATA_W - 1:0] filter_out,
    output reg output_valid
);

localparam signed [ACC_W-1:0] MAX_POS =  32767;
localparam signed [ACC_W-1:0] MAX_NEG = -32768;

reg signed [COEF_W-1:0] coeffs [0:NUM_TAPS-1];

initial begin
    $readmemh("coeffs.hex",coeffs);
end


wire signed [DATA_W+COEF_W-1:0] mult_prod [0:NUM_TAPS-1];
reg signed [ACC_W-1:0] acc_reg [0:NUM_TAPS-2]; // state/acc registers
reg signed [DATA_W-1:0] data_in_r;
always @(posedge clk) data_in_r <= data_in; // register data_in for timing optimization

genvar i;
generate
    for (i = 0; i < NUM_TAPS; i = i + 1)
    assign mult_prod[i] = data_in_r * coeffs[i];
endgenerate

integer j,k;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
    for (j = 0; j < NUM_TAPS-1; j = j + 1)
    acc_reg[j] <= {ACC_W{1'b0}}; 
    end else begin
    acc_reg[0] <= $signed(mult_prod[NUM_TAPS-1]); // data_in * coeffs[166]
    for (k = 1; k < NUM_TAPS - 1; k = k + 1)
    acc_reg[k] <= acc_reg[k-1] + $signed(mult_prod[NUM_TAPS-1-k]); 
    end
    end


wire signed [ACC_W-1:0] acc;
assign acc = acc_reg[NUM_TAPS-2] + mult_prod[0];
// Rounding
localparam signed [ACC_W - 1:0] HALF = 1 << (ACC_SHIFT-1); 
wire signed [ACC_W - 1:0] acc_abs = (acc < 0) ? -acc : acc;
wire signed [ACC_W - 1:0] acc_rounded = (acc_abs + HALF) >>> ACC_SHIFT;
wire signed [ACC_W - 1:0] result = (acc < 0 ) ? -acc_rounded : acc_rounded;

reg valid_pipe; // delay output valid by 2 clock cycles
always @(posedge clk or negedge rst_n) begin
if (!rst_n) begin
filter_out <= {DATA_W{1'b0}};
output_valid <= 1'b0;
valid_pipe <= 0;
end else begin
valid_pipe <= input_valid;
output_valid <= valid_pipe;
if (result > MAX_POS)
    filter_out <= MAX_POS;
else if (result < MAX_NEG)
    filter_out <= MAX_NEG;
else
    filter_out <= result;
end
end
endmodule