# Run from command line:
# julia train.jl
# julia train.jl --x 0.2
# julia train.jl --x 0.2 --noise 0.3
#
# Requires ArgParse:
#
# julia> import Pkg
# julia> Pkg.add("ArgParse")

using ArgParse

s = ArgParseSettings()
@add_arg_table! s begin
    "--x"
        arg_type = Float64
        default = 0.1
    "--noise"
        arg_type = Float64
        default = 0.1
end

args = parse_args(ARGS, s)
x = args["x"]
noise = args["noise"]

loss = (sin(5x) * (1 - tanh(x^2)) + randn() * noise)

println("loss:", loss)
