
DEFAULT_VALUES = {
            'layers': [
                {
                    'selection_type': 'splitmerge',
                    'value': {
                         'share': True,
                         'sequence': [
                             {'selection_type': 'expand_dim', 'value': -1},
                             {
                                 'selection_type': 'conv3d',
                                 'value': {'conv_outputs': 32, 'conv_X': 4, 'conv_Y': 4,
                                           'conv_T': 1, 'stride_X': 1, 'stride_Y': 1, 'stride_T': 1,
                                           'padding': 'valid', 'activation': 'relu'}
                             },
                             {
                                 'selection_type': 'conv3d',
                                 'value': {'conv_outputs': 4, 'conv_X': 4, 'conv_Y': 4,
                                           'conv_T': 32, 'stride_X': 1, 'stride_Y': 1, 'stride_T': 1,
                                           'padding': 'valid', 'activation': 'relu'}
                             },
                             {
                                 'selection_type': 'maxpool3d',
                                 'value': {
                                     'pool_X': 1, 'pool_Y': 1, 'pool_T': 16, 'stride_X': 1, 'stride_Y': 1,
                                     'stride_T': 1, 'padding': 'valid'}
                             },
                             {
                                 'selection_type': 'flatten', 'value': None
                             },
                             {
                                 'selection_type': 'dense',
                                 'value': {'units': 64, 'activation': 'relu'}
                             },
                             {
                                 'selection_type': 'dense',
                                 'value': {'units': 64, 'activation': 'relu'}
                             },
                             {
                                 'selection_type': 'dense',
                                 'value': {'units': 64, 'activation': 'relu'}
                             }
                         ]
                     }
                 }
            ],
            'output_mode': 'splitted_sigma'
        }