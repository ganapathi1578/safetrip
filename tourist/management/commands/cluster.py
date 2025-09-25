# myapp/management/commands/run_cluster_task.py
import time
import random
import torch
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from tourist.models import Tourist, TouristLocation, Cluster, ClusterMember
from tourist.constants import AIZAWL_PLACES


def get_random_location():
    """Pick a random Aizawl place with slight variation (~100m)."""
    place, (base_lat, base_lon) = random.choice(list(AIZAWL_PLACES.items()))
    lat = base_lat + random.uniform(-0.001, 0.001)
    lon = base_lon + random.uniform(-0.001, 0.001)
    return lat, lon, place


def pytorch_dbscan(X, eps=0.005, min_samples=2):
    """
    Simple DBSCAN implementation using PyTorch.
    X: tensor of shape [N, 2] (latitude, longitude)
    Returns labels (list of cluster ids)
    """
    N = X.size(0)
    labels = -torch.ones(N, dtype=torch.int32)  # -1 = noise
    cluster_id = 0

    visited = torch.zeros(N, dtype=torch.bool)

    for i in range(N):
        if visited[i]:
            continue
        visited[i] = True

        # compute distance to all points
        dist = torch.norm(X - X[i], dim=1)
        neighbors = (dist <= eps).nonzero(as_tuple=True)[0]

        if len(neighbors) < min_samples:
            labels[i] = -1  # noise
            continue

        labels[i] = cluster_id
        seeds = neighbors.tolist()
        seeds.remove(i)

        while seeds:
            j = seeds.pop(0)
            if not visited[j]:
                visited[j] = True
                dist_j = torch.norm(X - X[j], dim=1)
                neighbors_j = (dist_j <= eps).nonzero(as_tuple=True)[0]
                if len(neighbors_j) >= min_samples:
                    seeds.extend([n.item() for n in neighbors_j if labels[n] == -1])
            if labels[j] == -1:
                labels[j] = cluster_id
        cluster_id += 1

    return labels.tolist()


class Command(BaseCommand):
    help = "Continuously updates tourist locations and clusters them using PyTorch"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting cluster background task..."))

        while True:
            try:
                self.stdout.write("Updating tourist locations...")

                tourists = Tourist.objects.all()

                # Step 1: Add random location for each tourist
                for tourist in tourists:
                    lat, lon, place = get_random_location()
                    TouristLocation.objects.create(
                        tourist=tourist,
                        latitude=lat,
                        longitude=lon,
                        timestamp=timezone.now()
                    )

                # Step 2: Collect latest locations
                latest_locations = []
                tourists_list = []
                for t in tourists:
                    loc = t.locations.last()
                    if loc:
                        latest_locations.append([float(loc.latitude), float(loc.longitude)])
                        tourists_list.append(loc)

                if not latest_locations:
                    self.stdout.write("No locations found. Waiting 5 minutes...")
                    time.sleep(300)
                    continue

                X = torch.tensor(latest_locations, dtype=torch.float32)

                # Step 3: Apply PyTorch DBSCAN
                labels = pytorch_dbscan(X, eps=0.005, min_samples=2)

                # Step 4: Save clusters
                with transaction.atomic():
                    Cluster.objects.all().delete()  # Clear old clusters

                    for cluster_id in set(labels):
                        if cluster_id == -1:
                            continue  # skip noise

                        members = [tourists_list[i] for i in range(len(labels)) if labels[i] == cluster_id]

                        lat_center = sum([float(m.latitude) for m in members]) / len(members)
                        lon_center = sum([float(m.longitude) for m in members]) / len(members)

                        cluster = Cluster.objects.create(
                            cluster_id=cluster_id,
                            center_latitude=lat_center,
                            center_longitude=lon_center,
                            created_at=timezone.now()
                        )

                        for loc in members:
                            ClusterMember.objects.create(
                                cluster=cluster,
                                location=loc
                            )

                self.stdout.write(self.style.SUCCESS("Clustering completed. Waiting 5 minutes..."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error occurred: {e}"))

            # Step 5: Wait 5 minutes before next iteration
            time.sleep(300)
