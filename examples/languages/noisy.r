# Run from command line:
# Rscript train.R
# Rscript train.R --x 0.2
# Rscript train.R --x 0.2 --noise 0.3

suppressMessages(library(argparser))

p <- arg_parser("train")
p <- add_argument(p, "--x", help = "x", default = 0.1)
p <- add_argument(p, "--noise", help = "noise", default = 0.1)
argv <- parse_args(p)

x <- as.numeric(argv$x)
noise <- as.numeric(argv$noise)

loss <- (sin(5 * x) * (1 - tanh(x^2)) + rnorm(1) * noise)

cat("loss:", loss, "\n")
