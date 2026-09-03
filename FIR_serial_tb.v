`timescale 1ns/1ps
module FIR_serial_tb;

localparam NUM_TAPS = 167;
localparam N_SAMPLES = 129600;

reg clk;
reg rst_n;
reg sample_valid;
reg signed [15:0] sample_in;
wire signed [15:0] sample_out;
wire out_valid;

reg signed [15:0] stim [0:N_SAMPLES-1];
reg signed [15:0] gold [0:N_SAMPLES-1];

initial clk = 1'b0;

integer i , errors;
always begin
    #5 clk = ~clk;
end

fir_serial uut(
    .clk(clk),
    .rst_n(rst_n),
    .sample_valid(sample_valid),
    .sample_in(sample_in),
    .out_valid(out_valid),
    .sample_out(sample_out)
);

initial begin
    $dumpfile("firdump.vcd");
    $dumpvars(0,fir_serial);
    $readmemh("golden.hex", gold);
    $readmemh("stimulus.hex", stim);
end

initial begin
    errors = 0;
    rst_n = 1'b0;
    sample_in = 16'sd0;
    sample_valid = 1'b0;
    repeat(4) @(posedge clk);
    rst_n = 1'b1;
    @(posedge clk);

    for (i = 0; i < N_SAMPLES; i = i + 1) begin
    sample_in <= stim[i];
    sample_valid <= 1'b1;
    @(posedge clk);
    sample_valid <= 1'b0;
    wait(out_valid);
    @(posedge clk);

    if (sample_out !== gold[i]) begin
    errors = errors + 1;
    if (errors < 10)
    $display("MISMATCH i = %0d: got %d, expected %d", i,sample_out,gold[i]);
    end
    end
    $display("done: %0d errors out of %0d", errors, N_SAMPLES);
    $finish;
end
endmodule