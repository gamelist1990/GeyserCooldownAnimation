#!/usr/bin/env python3
"""Summarize actual Vulkan pipeline state and stencil draws from RenderDoc XML.

This is rendering evidence, not an automatic visual pass. Export XML with the
matching RenderDoc version before running. Resource IDs are capture-local.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def value(element, name):
    if element is None:
        return None
    node = element.find(f".//*[@name='{name}']")
    return None if node is None else node.get('string', node.text)


def summarize(source, output):
    root = ET.parse(source).getroot()
    pipelines, command_state, draws = {}, {}, []
    for chunk in root.find('chunks'):
        name = chunk.get('name')
        if name == 'vkCreateGraphicsPipelines':
            identifier = value(chunk, 'Pipeline')
            if identifier is None:
                raise ValueError('Missing pipeline resource in capture')
            depth = chunk.find(".//*[@name='pDepthStencilState']")
            faces = {}
            for face in ('front', 'back'):
                node = depth.find(f".//*[@name='{face}']") if depth is not None else None
                faces[face] = {} if node is None else {
                    child.get('name'): child.get('string', child.text) for child in node}
            pipelines[identifier] = {
                'cull': value(chunk, 'cullMode'),
                'depth_test': value(depth, 'depthTestEnable'),
                'depth_compare': value(depth, 'depthCompareOp'),
                'stencil_test': value(depth, 'stencilTestEnable'),
                'faces': faces,
                'color_masks': [node.get('string', node.text)
                    for node in chunk.findall(".//*[@name='colorWriteMask']")],
            }
        buffer = value(chunk, 'commandBuffer')
        if buffer is None:
            continue
        state = command_state.setdefault(buffer, {})
        if name == 'vkCmdBindPipeline':
            state['pipeline'] = value(chunk, 'pipeline')
        elif name in ('vkCmdSetStencilReference', 'vkCmdSetStencilWriteMask'):
            field = 'reference' if name.endswith('Reference') else 'writeMask'
            state[f'{field}_{value(chunk, "faceMask")}'] = value(chunk, field)
        elif name == 'vkCmdBindVertexBuffers2':
            state['vertex_bindings'] = {
                field: [node.text for node in chunk.find(f".//*[@name='{field}']")]
                for field in ('pBuffers', 'pOffsets', 'pStrides')}
        elif name == 'vkCmdDrawIndexed':
            pipeline = pipelines.get(state.get('pipeline'), {})
            if pipeline.get('faces', {}).get('front', {}).get('compareMask') != '128':
                continue
            draws.append({'chunk_index': int(chunk.get('chunkIndex')),
                'command_buffer': buffer, 'indices': value(chunk, 'indexCount'),
                'state': dict(state), 'pipeline_state': pipeline})
    report = {'source': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'driver': root.find('header/driver').text, 'pipelines': pipelines,
        'stencil_128_draws': draws, 'visual_status': 'review_required'}
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'pipelines': len(pipelines), 'stencil_128_draws': len(draws),
        'output': str(output)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    summarize(args.source, args.output)
