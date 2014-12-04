import argparse
import features
from models import gaussian, discrete, statistical

REGISTERED_MODELS = (gaussian.Simple, gaussian.Mixture, discrete.Histogram)
REGISTERED_PREPROCS = (statistical.Pearson,)

def get_base_parser():
    base_parser = argparse.ArgumentParser(add_help = False)
    base_parser.add_argument("-v", "--verbose", dest = "verbosity",
                             action = "store_const", const = 1, default = 0,
                             help = "Print basic debugging information.")

    base_parser.add_argument("-vv", "--debug", dest = "verbosity",
                             action = "store_const", const = 2,
                             help = "Print advanced debugging information.")

    base_parser.add_argument("-d", "--disable-rule", dest = "disabled_rules",
                             action = "append", metavar = 'rule',
                             help = "Disable a rule.")

    base_parser.set_defaults(disabled_rules = [])
    
    for model in REGISTERED_MODELS:
        model.register(base_parser)

    for preproc in REGISTERED_PREPROCS:
        preproc.register(base_parser)


    return base_parser

def get_sdtin_parser():
    parser = argparse.ArgumentParser(parents = [get_base_parser()],
                                     description="Loads a database from a text file, and reports outliers")
    parser.add_argument("input", nargs='?', default = "-", type = argparse.FileType('r'),
                        help = "Read data from file input. If omitted or '-', read from standard input.")
    
    parser.add_argument("-F", "--field-separator", dest = "fs",
                        action = "store", default = "\t", metavar = "fs",
                        help = "Use fs as the input field separator (default: tab).")

    return parser

def get_mimic_parser():
    parser = argparse.ArgumentParser(parents = [get_base_parser()],
                                     description="Loads the mimic2 database using sqlite3, and reports outliers")
    parser.add_argument("db", help = "Read data from sqlite3 database file db.")
    return parser

def load_models(namespace):
    models = []
    for model in REGISTERED_MODELS:
        params = getattr(namespace, model.ID)
        if params != None:
            models.append(model.from_parse(params))
    return models

def load_preprocs(namespace):
    preprocs = []
    for preproc in REGISTERED_PREPROCS:
        params = getattr(namespace, preproc.ID)
        if params != None:
            preprocs.append(preproc.from_parse(params))
    return preprocs

def parsewith(parser):
    args = parser.parse_args()
    models = load_models(args)
    preprocs = load_preprocs(args)
    if len(models) == 0:
        parser.error("No model specified!")
    if len(preprocs) == 0:
        parser.error("No preprocessors specified!")

    disabled_rules = set(args.disabled_rules)
    available_rules = set(r.__name__ for rs in features.rules.values() for r in rs)
    invalid_rules = disabled_rules - available_rules
    if len(invalid_rules) > 0:
        parser.error("Unknown rule(s) {}".format(", ".join(sorted(invalid_rules))))
    rules = {t: [r for r in rs if r.__name__ not in disabled_rules]
             for t, rs in features.rules.items()}

    return args, models, preprocs, rules
