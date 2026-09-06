module fir_serial #(
    parameter NUM_TAPS = 167,
    parameter DATA_W = 16,
    parameter COEF_W = 16,
    parameter ACC_W = 40,
    parameter ACC_SHIFT = 17
)(
    input wire clk, 
    input wire rst_n,
    input wire sample_valid,
    input wire signed [DATA_W - 1:0] sample_in,
    output reg out_valid,
    output reg signed [DATA_W - 1:0] sample_out

);

reg [7:0] wr_ptr; 
reg [7:0] tap_idx;
reg signed [ACC_W-1:0] acc;
reg signed [COEF_W-1:0] coeffs [0:NUM_TAPS-1]; // coefficient ROM
reg signed [DATA_W-1:0] buffer [0:NUM_TAPS-1]; // sample buffer

initial begin
    $readmemh("coeffs.hex",coeffs);
end

reg [7:0] rd_idx_r;

localparam IDLE = 2'd0, MAC = 2'd1, DONE = 2'd2;
reg [1:0] state;

localparam signed [ACC_W - 1:0] HALF = 1 << (ACC_SHIFT-1);
wire signed [ACC_W - 1:0] acc_abs = (acc < 0) ? -acc : acc;
wire signed [ACC_W - 1:0] acc_rounded = (acc_abs + HALF) >>> ACC_SHIFT;
wire signed [ACC_W - 1:0] result = (acc < 0 ) ? -acc_rounded : acc_rounded;


integer i;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < NUM_TAPS; i = i + 1)
        buffer[i] <= 0;
        state <= IDLE;
        wr_ptr <= 8'd0;
        tap_idx <= 8'd0;
        out_valid <= 1'b0;
        rd_idx_r <= 8'd0;
    end else begin
        out_valid <= 1'b0;
    case(state)
    IDLE: if (sample_valid) begin
        acc <= {ACC_W{1'b0}}; // clear accumulator before each MAC
        buffer[wr_ptr] <= sample_in;
        tap_idx <= 8'd0;
        state <= MAC;
        rd_idx_r <= wr_ptr;
    end
    MAC: begin
    acc <= acc + buffer[rd_idx_r] * coeffs[tap_idx]; // MAC
    if (tap_idx == NUM_TAPS - 1) begin
    state <= DONE; 
    end else begin
    tap_idx <= tap_idx + 1'b1;
    if (wr_ptr >= (tap_idx + 1'b1)) // pre compute rd_idx_r for the next cycle
    rd_idx_r <= wr_ptr - (tap_idx + 1'b1);
    else
    rd_idx_r <= wr_ptr + NUM_TAPS - (tap_idx + 1'b1);
        end
    end
    DONE: begin
        sample_out <= result[DATA_W-1:0];
        out_valid <= 1'b1;
        wr_ptr <= (wr_ptr == NUM_TAPS - 1) ? 0 : wr_ptr + 8'd1;
        state <= IDLE;
        end
        endcase
    end
end

endmodule