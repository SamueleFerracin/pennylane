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
"""
This file stores the conversions between gate base names and drawn labels
"""

non_parametric_qubit_labels = {
    'Hadamard': 'H',
    'PauliX': 'X',
    'PauliY': 'Y',
    'PauliZ': 'Z',
    'SX': '√X',
    'CZ': 'Z',
    'CY': 'Y',
}

parametric_qubit_labels = {
    'MultiRZ': "RZ",
    'PhaseShift': "Rϕ",
    'ControlledPhaseShift': "Rϕ",
    'CPhase': "Rϕ",
    "CRX": "RX",
    "CRY": "RY",
    "CRot": "Rot",
}

matrix_ops_labels = {
    'QubitUnitary': 'U',
    'ControlledQubitUnitary': 'U',
    'DiagonalQubitUnitary': 'U'
}

arithmetic_ops_labels = {
    'QubitSum': '+'
}

cv_labels = {
    "Beamsplitter": "BS",
    "Squeezing": "S",
    "TwoModeSqueezing": "S",
    "Displacement": "D",
    "NumberOperator": "n",
    "Rotation": "R",
    "ControlledAddition": "X",
    "ControlledPhase": "Z",
    "ThermalState": "Thermal",
    "GaussianState": "Gaussian",
    "QuadraticPhase": "P",
    "CubicPhase": "V",
    "X": "x",
    "P": "p",
}

label_dicts_list= [non_parametric_qubit_labels, parametric_qubit_labels, matrix_ops_labels,
               arithmetic_ops_labels, cv_labels]

label_dict = {}
for d in label_dicts_list:
    label_dict.update(d)
