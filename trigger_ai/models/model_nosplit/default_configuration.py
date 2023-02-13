# Raw form data
DEFAULT_CONF = {
            'common': [
                {'selection_type': 'expand_dim', 'value': -1},
                {'selection_type': 'conv3d',
                 'value': {
                     'conv_outputs': 1,
                     'conv_X': 3,
                     'conv_Y': 3,
                     'conv_T': 8,
                     'stride_X': 1,
                     'stride_Y': 1,
                     'stride_T': 1,
                     'padding': 'valid',
                     'activation': 'relu'}},
                {'selection_type': 'maxpool3d',
                 'value': {'pool_X': 2, 'pool_Y': 2, 'pool_T': 16,
                           'stride_X': 1, 'stride_Y': 1, 'stride_T': 1,
                           'padding': 'valid'}
                 },
                {'selection_type': 'flatten', 'value': None},
                {'selection_type': 'dense',
                 'value': {'units': 64, 'activation': 'relu'}
                 }
            ]
        }
