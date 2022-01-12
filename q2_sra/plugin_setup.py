#   Copyright 2021 Evan Bolyen
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import importlib

from qiime2.plugin import (Plugin, SemanticType, model, Metadata, Str,
                           Bool, Int, Range, Choices, TypeMap)

from q2_types.sample_data import SampleData
from q2_types.per_sample_sequences import (
    SequencesWithQuality, PairedEndSequencesWithQuality,
    JoinedSequencesWithQuality)

import q2_sra.actions as actions
from q2_sra.format_types import MetadataFormat, MetadataDirFmt, SRAMetadata


# This is the plugin object. It is what the framework will load and what an
# interface will interact with. Basically every registration we perform will
# involve this object in some way.
plugin = Plugin("sra", version="0.0.1.dev",
                website="https://github.com/ebolyen/q2-sra")

plugin.register_formats(MetadataFormat, MetadataDirFmt)
plugin.register_semantic_types(SRAMetadata)

plugin.register_semantic_type_to_format(SampleData[SRAMetadata],
                                        artifact_format=MetadataDirFmt)

T_type, T_output = TypeMap({
    Choices('single'): SequencesWithQuality,
    Choices('paired'): PairedEndSequencesWithQuality,
    Choices('joined'): JoinedSequencesWithQuality,
    #Choices('sra-etl'): SRA_ETL
})

plugin.methods.register_function(
    function=actions.fetch_runs,
    inputs={},
    parameters={
        'accessions': Metadata,
        'type': Str % T_type,
        'where': Str,
        'col': Str,
        'skip_missing': Bool,
        'batch_size': Int % Range(1, 600),
    },
    outputs=[
        ('demux', SampleData[T_output]),
        ('metadata', SampleData[SRAMetadata])
    ],
    input_descriptions={},
    parameter_descriptions={},
    name='Fetch SRA Sequences (SRR ids)',
    description="..."
)

plugin.methods.register_function(
    function=actions.fetch_bioproject,
    inputs={},
    parameters={
        'bioproject': Str,
        'type': Str % T_type,
        'batch_size': Int % Range(1, 600),
    },
    outputs=[
        ('demux', SampleData[T_output]),
        ('metadata', SampleData[SRAMetadata])
    ],
    input_descriptions={},
    parameter_descriptions={},
    name='Fetch BioProject runs',
    description="..."
)

importlib.import_module("q2_sra.transformers")
