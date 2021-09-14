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


import pytest

import pennylane as qml
from pennylane.circuit_drawer.gate_label import gate_label


mat2x2 = qml.numpy.array([[1, 0], [0,1]])


test_cases_false = [(qml.S(wires=0), "S"), # no parameters, not in gate data
                    (qml.PauliX(0), "X"), # no parameters, in gate data
                    (qml.RX(1.23456, wires=0), "RX"), # one parameter, not in gate data
                    (qml.PhaseShift(1.23456, wires=0), 'Rϕ'), # one parameter, in gate data
                    (qml.U3(1.1111, 2.2222, 3.3333, wires=0), "U3"), # multiple parameters
                    (qml.QubitUnitary(mat2x2, wires=0), "U") # matrix input
]

@pytest.mark.parametrize("op, expected", test_cases_false)
def test_no_parameters(op, expected):
    assert gate_label(op, False) == expected
    assert gate_label(op.inv(), False) == (expected+'⁻¹')

test_cases_true_2 = [(qml.S(wires=0), "S"), # no parameters, not in gate data
                    (qml.PauliX(0), "X"), # no parameters, in gate data
                    (qml.RX(1.23456, wires=0), "RX(1.23)"), # one parameter, not in gate data
                    (qml.PhaseShift(1.23456, wires=0), 'Rϕ(1.23)'), # one parameter, in gate data
                    (qml.U3(1.1111, 2.2222, 3.3333, wires=0), "U3(1.11,2.22,3.33)"), # multiple parameters
                    (qml.QubitUnitary(mat2x2, wires=0), "U") # matrix input
]

@pytest.mark.parametrize("op, expected", test_cases_true_2)
def test_include_parameters_2_decimals(op, expected):
    assert gate_label(op, True, 2) == expected
    assert gate_label(op.inv(), True, 2) == (expected+'⁻¹')

@pytest.mark.parametrize("decimals,expected", ((0, "1"), (1, "1.2"), (2, "1.23")))
def test_decimals(decimals, expected):

    out = gate_label(qml.RX(1.23456, wires=0), include_parameters=True, decimal_places=decimals)

    assert out == f"RX({expected})"
