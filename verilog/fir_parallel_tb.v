module fir_parallel_tb;
reg clk;
reg rst_n;
reg input_valid;
reg signed [15:0] data_in;

wire output_valid;
wire signed [15:0] filter_out;

localparam N_SAMPLES = 42000;
reg signed [15:0] stim [0:N_SAMPLES-1];
reg signed [15:0] gold [0:N_SAMPLES-1];

initial clk = 0;
integer i , errors;
always begin
    #5 clk = ~clk;
end

fir_parallel dut(
.clk(clk),
.rst_n(rst_n),
.input_valid(input_valid),
.data_in(data_in),
.output_valid(output_valid),
.filter_out(filter_out)
);

initial begin
    $dumpfile("fir_parallel.vcd");
    $dumpvars(0,fir_parallel_tb);
    $readmemh("golden.hex", gold);
    $readmemh("stimulus.hex", stim);
end

integer in_idx, out_idx;

initial begin
    rst_n = 1'b0;
    repeat(4) @(posedge clk);
    rst_n = 1'b1;
end
// feed one sample per clock continuously
always @(posedge clk) begin
    if (!rst_n) begin
        in_idx      <= 0;
        input_valid <= 1'b0;
        data_in     <= 0;
    end else if (in_idx < N_SAMPLES) begin
        data_in     <= stim[in_idx];
        input_valid <= 1'b1;
        in_idx      <= in_idx + 1;
    end else begin
        input_valid <= 1'b0;
    end
end

// check whenever an output appears
always @(posedge clk) begin
    if (!rst_n) begin
        out_idx <= 0;
        errors  <= 0;
    end else if (output_valid) begin
        if (filter_out !== gold[out_idx]) begin
            errors <= errors + 1;
            if (errors < 10)
                $display("MISMATCH %0d: got %d expected %d",
                         out_idx, filter_out, gold[out_idx]);
        end
        out_idx <= out_idx + 1;
        if (out_idx == N_SAMPLES-1) begin
            $display("done: %0d errors out of %0d", errors, N_SAMPLES);
            $finish;
        end
    end
end


endmodule