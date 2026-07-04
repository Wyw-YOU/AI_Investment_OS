from app.engine.graph import build_analysis_graph, GraphState

graph = build_analysis_graph()
compiled = graph.compile()
print('Graph compiled successfully!')
print(f'State type: {GraphState.__name__}')
print(f'Nodes: {list(compiled.get_graph().nodes.keys())}')