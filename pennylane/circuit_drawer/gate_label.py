# Copyright 2018-2021 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pennylane as qml

from pennylane.math import shape
from pennylane.operation import ObservableReturnTypes

from .gate_label_data import label_dict


def gate_label(op, include_parameters=False, decimal_places=2):
    """Produces a label for a given gate.
    
    Args:
        op (~.Operation): PennyLane label to produce the label for

    Keyword Args:
        include_parameters=False (Bool): Whether or not to include parameters in label
        decimal_places=2 (Int): If parameters are included, how many decimals to include

    Returns:
        str
    """
    base = label_dict.get(op.base_name, op.base_name)
    
    if op.inverse:
        end = "⁻¹"
    else:
        end = ""
    
    if not include_parameters:
        return base+end
    
    params = op.parameters
    if len(params) == 0:
        return base+end

    if len(params) == 1:
        # don't print if matrix parameter
        if len(shape(params[0])) != 0:
            return base+end
        return base+f'({params[0]:.{decimal_places}f})'+end

    param_string = ",".join(f"{p:.{decimal_places}f}" for p in params)
    return f"{base}({param_string}){end}"


def measurement_label(obs):
    """Produces a label for a measurement.
    
    Args:
        obs (~.measure.MeasurementProcess)
    
    Returns:
        str
    """
    if obs.return_type == ObservableReturnTypes.Expectation:
        if isinstance(obs.obs, qml.Projector):
            state = obs.obs.parameters[0]
            state_str = "".join([f"{int(i)}" for i in state])
            return f"|{state_str}⟩⟨{state_str}|"

        if isinstance(obs.obs, qml.FockStateProjector):
            n = obs.obs.data[0]
            return f"|{n}⟩⟨{n}|"

        return "⟨n⟩"

        name = label_dict.get(obs.obs.name, obs.obs.name)
        return f"⟨{name}⟩"
    if obs.return_type == ObservableReturnTypes.Variance:
        name = label_dict.get(obs.obs.name, obs.obs.name)
        return f"Var[{name}]"
    return obs.return_type.name