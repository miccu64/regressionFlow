from .odefunc import ODEfunc, ODEnet, ODEHypernet, ODEhyperfunc, ODEHypernet2D, ODEhyperfunc2D
from .normalization import MovingBatchNorm1d
from .cnf import CNF, SequentialFlow, CNF2D


def count_nfe(model):
    class AccNumEvals(object):

        def __init__(self):
            self.num_evals = 0

        def __call__(self, module):
            if isinstance(module, CNF):
                self.num_evals += module.num_evals()

    accumulator = AccNumEvals()
    model.apply(accumulator)
    return accumulator.num_evals


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def count_total_time(model):
    class Accumulator(object):

        def __init__(self):
            self.total_time = 0

        def __call__(self, module):
            if isinstance(module, CNF):
                self.total_time = self.total_time + module.sqrt_end_time * module.sqrt_end_time

    accumulator = Accumulator()
    model.apply(accumulator)
    return accumulator.total_time


def build_model(args, input_dim, hidden_dims, context_dim, num_blocks, conditional):
    def build_cnf():
        diffeq = ODEnet(
            hidden_dims=hidden_dims,
            input_shape=(input_dim,),
            context_dim=context_dim,
            layer_type=args.layer_type,
            nonlinearity=args.nonlinearity,
        )
        odefunc = ODEfunc(
            diffeq=diffeq,
        )
        cnf = CNF(
            odefunc=odefunc,
            T=args.time_length,
            train_T=args.train_T,
            conditional=conditional,
            solver=args.solver,
            use_adjoint=args.use_adjoint,
            atol=args.atol,
            rtol=args.rtol,
        )
        return cnf

    chain = [build_cnf() for _ in range(num_blocks)]
    if args.batch_norm:
        bn_layers = [MovingBatchNorm1d(input_dim, bn_lag=args.bn_lag, sync=args.sync_bn)
                     for _ in range(num_blocks)]
        bn_chain = [MovingBatchNorm1d(input_dim, bn_lag=args.bn_lag, sync=args.sync_bn)]
        for a, b in zip(chain, bn_layers):
            bn_chain.append(a)
            bn_chain.append(b)
        chain = bn_chain
    model = SequentialFlow(chain)

    return model


def build_hyper(args, num_blocks, conditional):
    def build_cnf():
        diffeq = ODEHypernet(
            dims=args.dims,
            input_dim=args.input_dim,
            nonlinearity=args.nonlinearity,
        )
        odefunc = ODEhyperfunc(
            use_div_approx_train=args.use_div_approx_train,
            use_div_approx_test=args.use_div_approx_test,
            diffeq=diffeq,
        )
        cnf = CNF(
            odefunc=odefunc,
            T=args.time_length,
            train_T=args.train_T,
            conditional=conditional,
            solver=args.solver,
            use_adjoint=args.use_adjoint,
            atol=args.atol,
            rtol=args.rtol,
        )
        return cnf

    chain = [build_cnf() for _ in range(num_blocks)]
    if args.batch_norm:
        features_count = args.output_size
        if features_count is None:
            features_count = args.input_dim

        bn_layers = [MovingBatchNorm1d(features_count, bn_lag=args.bn_lag, sync=args.sync_bn)
                     for _ in range(num_blocks)]
        bn_chain = [MovingBatchNorm1d(features_count, bn_lag=args.bn_lag, sync=args.sync_bn)]
        for a, b in zip(chain, bn_layers):
            bn_chain.append(a)
            bn_chain.append(b)
        chain = bn_chain
    model = SequentialFlow(chain)

    return model


def build_hyper2D(args, num_blocks, conditional):
    def build_cnf():
        diffeq = ODEHypernet2D(
            dims=args.dims,
            input_dim=args.input_dim,
            nonlinearity=args.nonlinearity,
        )
        odefunc = ODEhyperfunc2D(
            diffeq=diffeq,
        )
        cnf = CNF2D(
            odefunc=odefunc,
            T=args.time_length,
            train_T=args.train_T,
            conditional=conditional,
            solver=args.solver,
            use_adjoint=args.use_adjoint,
            atol=args.atol,
            rtol=args.rtol,
        )
        return cnf

    chain = [build_cnf() for _ in range(num_blocks)]
    if args.batch_norm:
        bn_layers = [MovingBatchNorm1d(args.input_dim, bn_lag=args.bn_lag, sync=args.sync_bn)
                     for _ in range(num_blocks)]
        bn_chain = [MovingBatchNorm1d(args.input_dim, bn_lag=args.bn_lag, sync=args.sync_bn)]
        for a, b in zip(chain, bn_layers):
            bn_chain.append(a)
            bn_chain.append(b)
        chain = bn_chain
    model = SequentialFlow(chain)

    return model


def get_point_cnf(args):
    dims = tuple(map(int, args.dims.split("-")))
    model = build_model(args, args.input_dim, dims, args.zdim, args.num_blocks, True).cuda()
    print("Number of trainable parameters of Point CNF: {}".format(count_parameters(model)))
    return model


def get_latent_cnf(args):
    dims = tuple(map(int, args.latent_dims.split("-")))
    model = build_model(args, args.zdim, dims, 0, args.latent_num_blocks, False).cuda()
    print("Number of trainable parameters of Latent CNF: {}".format(count_parameters(model)))
    return model


def get_hyper_cnf(args):
    model = build_hyper(args, args.num_blocks, True).cuda()
    return model

def get_hyper_cnf2D(args):
    model = build_hyper2D(args, args.num_blocks, True).cuda()
    return model
