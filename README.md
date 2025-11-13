# UAV Strategic Deconfliction in Shared Airspace

This repository implements a **strategic deconfliction system** that checks whether a primary drone’s waypoint mission is safe to fly in shared airspace, by comparing it against simulated flight paths of other drones in **space and time**.

The system includes:

- A core **deconfliction engine** (spatio-temporal conflict checks)
- **Trajectory interpolation** from waypoints
- **Static 2D plots**, **2D animations**, and **interactive 3D plots**
- A **CLI** for running analyses and generating reports/visuals
- A full **pytest** test suite (already passing)

---

## 1. Quick Start

### 1.1. Clone and enter the repo

```bash
git clone <your-repo-url> uav_deconflict
cd uav_deconflict
```
