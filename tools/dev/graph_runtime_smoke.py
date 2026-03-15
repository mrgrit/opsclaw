from packages.graph_runtime import build_minimal_project_graph, get_next_stage


def main() -> int:
    graph = build_minimal_project_graph()
    print("STAGES:", ",".join(graph["stages"]))
    print("NEXT_INTAKE:", get_next_stage("intake"))
    print("NEXT_PLAN:", get_next_stage("plan"))
    print("NEXT_EXECUTE:", get_next_stage("execute"))
    print("NEXT_VALIDATE:", get_next_stage("validate"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
