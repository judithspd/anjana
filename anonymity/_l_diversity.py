# -*- coding: utf-8 -*-

# Copyright 2024 Spanish National Research Council (CSIC)
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import typing
import numpy as np
import pandas as pd
import pycanon
from anonymity.utils import utils
from copy import copy
from anonymity import k_anonymity_aux


def l_diversity(
    data: pd.DataFrame,
    ident: typing.Union[typing.List, np.ndarray],
    quasi_ident: typing.Union[typing.List, np.ndarray],
    sens_att: str,
    k: int,
    l_div: int,
    supp_level: float,
    hierarchies: dict,
) -> pd.DataFrame:
    """Anonymize a dataset using l-diversity.

    :param data: data under study.
    :type data: pandas dataframe

    :param ident: list with the name of the columns of the dataframe
        that are identifiers.
    :type ident: list of strings

    :param quasi_ident: list with the name of the columns of the dataframe
        that are quasi-identifiers.
    :type quasi_ident: list of strings

    :param sens_att: string with the name of the sensitive attribute.
    :type sens_att: string

    :param k: desired level of k-anonymity.
    :type k: int

    :param l_div: desired level of l-diversity.
    :type l_div: int

    :param supp_level: maximum level of record suppression allowed
        (from 0 to 100).
    :type supp_level: float

    :param hierarchies: hierarchies for generalizing the QI.
    :type hierarchies: dictionary containing one dictionary for QI
        with the hierarchies and the levels

    :return: anonymized data.
    :rtype: pandas dataframe
    """
    data_kanon, supp_records, gen_level = k_anonymity_aux(
        data, ident, quasi_ident, k, supp_level, hierarchies
    )

    l_real = pycanon.anonymity.l_diversity(data_kanon, quasi_ident, [sens_att])
    quasi_ident_gen = copy(quasi_ident)

    if l_real >= l_div:
        print(f"The data verifies l-diversity with l={l_real}")
        return data_kanon

    while l_real < l_div:
        equiv_class = pycanon.anonymity.utils.aux_anonymity.get_equiv_class(
            data_kanon, quasi_ident
        )
        ec_sensitivity = [
            len(np.unique(data_kanon.iloc[ec][sens_att])) for ec in equiv_class
        ]

        if l_div > max(ec_sensitivity):
            data_ec = pd.DataFrame({"equiv_class": equiv_class, "l": ec_sensitivity})
            data_ec_l = data_ec[data_ec.l < l_div]
            records_sup = sum(data_ec_l.l.values)
            if (records_sup + supp_records) * 100 / len(data) <= supp_level:
                ec_elim = np.concatenate(
                    [
                        pycanon.anonymity.utils.aux_functions.convert(ec)
                        for ec in data_ec_l.equiv_class.values
                    ]
                )
                anonim_data = data_kanon.drop(ec_elim).reset_index()
                l_supp = pycanon.anonymity.l_diversity(
                    anonim_data, quasi_ident, [sens_att]
                )
                if l_supp >= l_div:
                    return anonim_data

        if len(quasi_ident_gen) == 0:
            print(f"l-diversity cannot be achieved for l={l_div}")
            return data_kanon

        qi_gen = quasi_ident_gen[
            np.argmax([len(np.unique(data_kanon[qi])) for qi in quasi_ident_gen])
        ]

        try:
            generalization_qi = utils.apply_hierarchy(
                data_kanon[qi_gen].values, hierarchies[qi_gen], gen_level[qi_gen] + 1
            )
            data_kanon[qi_gen] = generalization_qi
            gen_level[qi_gen] = gen_level[qi_gen] + 1
        except ValueError:
            if qi_gen in quasi_ident_gen:
                quasi_ident_gen.remove(qi_gen)

        l_real = pycanon.anonymity.l_diversity(data_kanon, quasi_ident, [sens_att])
        if l_real >= l_div:
            return data_kanon

    return data_kanon


def entropy_l_diversity(
    data: pd.DataFrame,
    ident: typing.Union[typing.List, np.ndarray],
    quasi_ident: typing.Union[typing.List, np.ndarray],
    sens_att: str,
    k: int,
    l_div: int,
    supp_level: float,
    hierarchies: dict,
) -> pd.DataFrame:
    """Anonymize a dataset using entropy l-diversity.

    :param data: data under study.
    :type data: pandas dataframe

    :param ident: list with the name of the columns of the dataframe
        that are identifiers.
    :type ident: list of strings

    :param quasi_ident: list with the name of the columns of the dataframe
        that are quasi-identifiers.
    :type quasi_ident: list of strings

    :param sens_att: string with the name of the sensitive attribute.
    :type sens_att: string

    :param k: desired level of k-anonymity.
    :type k: int

    :param l_div: desired level of entropy l-diversity.
    :type l_div: int

    :param supp_level: maximum level of record suppression allowed
        (from 0 to 100).
    :type supp_level: float

    :param hierarchies: hierarchies for generalizing the QI.
    :type hierarchies: dictionary containing one dictionary for QI
        with the hierarchies and the levels

    :return: anonymized data.
    :rtype: pandas dataframe
    """
    data_kanon, supp_records, gen_level = k_anonymity_aux(
        data, ident, quasi_ident, k, supp_level, hierarchies
    )

    l_real = pycanon.anonymity.entropy_l_diversity(data_kanon, quasi_ident, [sens_att])
    quasi_ident_gen = copy(quasi_ident)

    if l_real >= l_div:
        print(f"The data verifies entropy l-diversity with l={l_real}")
        return data_kanon

    while l_real < l_div:
        if len(quasi_ident_gen) == 0:
            print(f"Entropy l-diversity cannot be achieved for l={l_div}")
            return data_kanon

        qi_gen = quasi_ident_gen[
            np.argmax([len(np.unique(data_kanon[qi])) for qi in quasi_ident_gen])
        ]

        try:
            generalization_qi = utils.apply_hierarchy(
                data_kanon[qi_gen].values, hierarchies[qi_gen], gen_level[qi_gen] + 1
            )
            data_kanon[qi_gen] = generalization_qi
            gen_level[qi_gen] = gen_level[qi_gen] + 1
        except ValueError:
            if qi_gen in quasi_ident_gen:
                quasi_ident_gen.remove(qi_gen)

        l_real = pycanon.anonymity.entropy_l_diversity(
            data_kanon, quasi_ident, [sens_att]
        )
        if l_real >= l_div:
            return data_kanon

    return data_kanon


def recursive_c_l_diversity(
    data: pd.DataFrame,
    ident: typing.Union[typing.List, np.ndarray],
    quasi_ident: typing.Union[typing.List, np.ndarray],
    sens_att: str,
    k: int,
    c: int,
    l_div: int,
    supp_level: float,
    hierarchies: dict,
) -> pd.DataFrame:
    """Anonymize a dataset using recursive (c,l)-diversity.

    :param data: data under study.
    :type data: pandas dataframe

    :param ident: list with the name of the columns of the dataframe
        that are identifiers.
    :type ident: list of strings

    :param quasi_ident: list with the name of the columns of the dataframe
        that are quasi-identifiers.
    :type quasi_ident: list of strings

    :param sens_att: string with the name of the sensitive attribute.
    :type sens_att: string

    :param k: desired level of k-anonymity.
    :type k: int

    :param c: desired value of c for recursive (c,l)-diversity.
    :type c: int

    :param l_div: desired level of l-diversity.
    :type l_div: int

    :param supp_level: maximum level of record suppression allowed
        (from 0 to 100).
    :type supp_level: float

    :param hierarchies: hierarchies for generalizing the QI.
    :type hierarchies: dictionary containing one dictionary for QI
        with the hierarchies and the levels

    :return: anonymized data.
    :rtype: pandas dataframe
    """

    data_kanon, supp_records, gen_level = k_anonymity_aux(
        data, ident, quasi_ident, k, supp_level, hierarchies
    )

    c_real, l_real = pycanon.anonymity.recursive_c_l_diversity(
        data_kanon, quasi_ident, [sens_att]
    )
    quasi_ident_gen = copy(quasi_ident)

    if l_real >= l_div and c_real >= c:
        print(
            f"The data verifies recursive (c,l)-diversity with l={l_real}, c={c_real}"
        )
        return data_kanon

    while l_real < l_div or c_real < c:
        if len(quasi_ident_gen) == 0:
            print(
                f"Recursive (c,l)-diversity cannot be achieved for l={l_div} and c={c}"
            )
            return data_kanon

        qi_gen = quasi_ident_gen[
            np.argmax([len(np.unique(data_kanon[qi])) for qi in quasi_ident_gen])
        ]

        try:
            generalization_qi = utils.apply_hierarchy(
                data_kanon[qi_gen].values, hierarchies[qi_gen], gen_level[qi_gen] + 1
            )
            data_kanon[qi_gen] = generalization_qi
            gen_level[qi_gen] = gen_level[qi_gen] + 1
        except ValueError:
            if qi_gen in quasi_ident_gen:
                quasi_ident_gen.remove(qi_gen)

        c_real, l_real = pycanon.anonymity.recursive_c_l_diversity(
            data_kanon, quasi_ident, [sens_att]
        )
        if l_real >= l_div and c_real >= c:
            return data_kanon

    return data_kanon
