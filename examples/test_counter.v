`timescale 1ns / 1ps
module test_counter();
    reg clk, rst;
    reg [3:0] count;
    wire [6:0] seg;
    
    initial begin
        clk = 0;
        rst = 0;
        #15 rst = 1;
    end
    
    always #5 clk = ~clk;
    
    always @(posedge clk or negedge rst) begin
        if (~rst) count <= 0;
        else count <= count + 1;
    end
    
    assign seg = (count == 0) ? 7'b0111111 :
                 (count == 1) ? 7'b0000110 :
                 (count == 2) ? 7'b1011011 :
                 (count == 3) ? 7'b1001111 : 7'b0000000;
    
    initial begin
        $dumpfile("counter.vcd");
        $dumpvars(0, test_counter);
        #200 $finish;
    end
endmodule
