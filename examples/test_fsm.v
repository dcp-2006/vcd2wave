`timescale 1ns / 1ps
module test_fsm();
    reg clk, rst;
    reg [1:0] state;
    reg [1:0] next_state;
    reg [3:0] data;
    wire [3:0] result;
    
    parameter S_IDLE = 2'b00, S_LOAD = 2'b01, S_CALC = 2'b10, S_DONE = 2'b11;
    
    initial begin
        clk = 0;
        rst = 0;
        #12 rst = 1;
    end
    
    always #5 clk = ~clk;
    
    always @(*) begin
        case (state)
            S_IDLE: next_state = S_LOAD;
            S_LOAD: next_state = S_CALC;
            S_CALC: next_state = S_DONE;
            S_DONE: next_state = S_IDLE;
            default: next_state = S_IDLE;
        endcase
    end
    
    always @(posedge clk or negedge rst) begin
        if (~rst) begin
            state <= S_IDLE;
            data <= 0;
        end else begin
            state <= next_state;
            if (state == S_LOAD) data <= data + 5;
        end
    end
    
    assign result = data * 2;
    
    initial begin
        $dumpfile("fsm.vcd");
        $dumpvars(0, test_fsm);
        #200 $finish;
    end
endmodule
