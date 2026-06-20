document.addEventListener('DOMContentLoaded', async () => {
    // Add upload event listener
    const uploadInput = document.getElementById('csv-upload');
    if (uploadInput) {
        uploadInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const btn = document.getElementById('upload-btn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '⏳ Processing...';
            btn.classList.add('opacity-50', 'cursor-not-allowed');
            btn.disabled = true;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (res.ok) {
                    window.location.reload();
                } else {
                    const err = await res.json();
                    alert('Upload failed: ' + (err.error || 'Unknown error'));
                }
            } catch (err) {
                console.error(err);
                alert('Upload failed due to network error.');
            } finally {
                btn.innerHTML = originalText;
                btn.classList.remove('opacity-50', 'cursor-not-allowed');
                btn.disabled = false;
                e.target.value = '';
            }
        });
    }

    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        // Update top cards dynamically
        const overviewContainer = document.getElementById('overview-cards');
        if (overviewContainer) {
            overviewContainer.innerHTML = `
                <div class="glass-card p-5" id="card-damage">
                    <h3 class="text-sm text-gray-400 font-medium">Most Claimed Damage</h3>
                    <p class="text-3xl font-bold mt-2 text-white value">${data.most_claimed_damage || 'N/A'}</p>
                </div>
                <div class="glass-card p-5" id="card-risk">
                    <h3 class="text-sm text-gray-400 font-medium">Risky Users</h3>
                    <p class="text-3xl font-bold mt-2 text-red-400 value">${data.most_risky_users || '0'}</p>
                </div>
                <div class="glass-card p-5" id="card-contradiction">
                    <h3 class="text-sm text-gray-400 font-medium">Contradictions</h3>
                    <p class="text-3xl font-bold mt-2 text-yellow-400 value">${data.most_common_contradictions || '0'}</p>
                </div>
                <div class="glass-card p-5" id="card-quality">
                    <h3 class="text-sm text-gray-400 font-medium">Avg Evidence Quality</h3>
                    <p class="text-3xl font-bold mt-2 text-green-400 value">${(data.evidence_quality_avg || '0') + '%'}</p>
                </div>
            `;
        }

        // Populate table
        const tbody = document.querySelector('#claims-table tbody');
        tbody.innerHTML = '';
        
        data.recent_claims.forEach(claim => {
            const tr = document.createElement('tr');
            
            let statusClass = 'supported';
            if (claim.status === 'contradicted') statusClass = 'contradicted';
            if (claim.status === 'insufficient_evidence') statusClass = 'insufficient';

            // Escape quotes for the title attribute
            const safeText = claim.text.replace(/"/g, '&quot;');

            tr.innerHTML = `
                <td class="py-3">${claim.claim_id}</td>
                <td class="py-3">${claim.user_id}</td>
                <td class="py-3"><div class="truncate max-w-md" title="${safeText}">"${claim.text}"</div></td>
                <td class="py-3"><span class="status ${statusClass}">${claim.status}</span></td>
                <td class="py-3">${claim.severity}</td>
            `;
            tbody.appendChild(tr);
        });

        // Fetch and render the graph
        renderGraph();

    } catch (error) {
        console.error('Failed to load dashboard data:', error);
        document.querySelectorAll('.value').forEach(el => {
            el.textContent = 'Error';
            el.classList.remove('loading');
        });
    }
});

async function renderGraph() {
    try {
        const res = await fetch('/api/graph');
        const graphData = await res.json();
        
        if (!graphData.nodes || graphData.nodes.length === 0) return;

        const container = document.getElementById('graph-container');
        const width = container.clientWidth;
        const height = container.clientHeight;

        const svg = d3.select("#graph-container")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
            
        // Tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("position", "absolute")
            .style("visibility", "hidden")
            .style("background", "rgba(0, 0, 0, 0.8)")
            .style("color", "#fff")
            .style("padding", "8px")
            .style("border-radius", "4px")
            .style("font-size", "12px")
            .style("border", "1px solid rgba(255,255,255,0.2)")
            .style("pointer-events", "none")
            .style("z-index", "100");

        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(180))
            .force("charge", d3.forceManyBody().strength(-800))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide().radius(40).iterations(4));

        const link = svg.append("g")
            .attr("stroke", "rgba(255,255,255,0.2)")
            .attr("stroke-opacity", 0.6)
            .selectAll("line")
            .data(graphData.links)
            .join("line")
            .attr("stroke-width", d => Math.max(1, Math.sqrt(d.value)));

        const colorScale = d3.scaleOrdinal()
            .domain([0, 1, 2, 3, 4])
            .range(["#6d28d9", "#0ea5e9", "#22c55e", "#eab308", "#ef4444"]);

        const node = svg.append("g")
            .attr("stroke", "rgba(255,255,255,0.5)")
            .attr("stroke-width", 2)
            .selectAll("circle")
            .data(graphData.nodes)
            .join("circle")
            .attr("r", d => d.group === 0 ? 20 : (d.group === 4 ? 12 : 10))
            .attr("fill", d => colorScale(d.group))
            .style("filter", "drop-shadow(0 0 8px rgba(255,255,255,0.2))")
            .call(drag(simulation))
            .on("mouseover", (event, d) => {
                tooltip.style("visibility", "visible").text(d.label || d.id);
                d3.select(event.currentTarget).attr("stroke", "#fff").attr("stroke-width", 3);
            })
            .on("mousemove", (event) => {
                tooltip.style("top", (event.pageY - 10) + "px").style("left", (event.pageX + 10) + "px");
            })
            .on("mouseout", (event) => {
                tooltip.style("visibility", "hidden");
                d3.select(event.currentTarget).attr("stroke", "rgba(255,255,255,0.5)").attr("stroke-width", 2);
            });

        const labels = svg.append("g")
            .selectAll("text")
            .data(graphData.nodes)
            .join("text")
            .attr("dy", -16)
            .attr("dx", 0)
            .attr("text-anchor", "middle")
            .attr("font-size", "11px")
            .attr("font-weight", "500")
            .attr("fill", "rgba(255,255,255,0.8)")
            .text(d => d.group === 0 || d.group === 4 ? d.label : d.label.substring(0, 15) + (d.label.length > 15 ? '...' : ''))
            .style("pointer-events", "none");

        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("cx", d => d.x = Math.max(20, Math.min(width - 20, d.x)))
                .attr("cy", d => d.y = Math.max(20, Math.min(height - 20, d.y)));
                
            labels
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        });

        function drag(simulation) {
            function dragstarted(event) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }
            function dragged(event) {
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }
            function dragended(event) {
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }
            return d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended);
        }

    } catch (err) {
        console.error("Error rendering graph:", err);
    }
}

function initThreeJS() {
    const container = document.getElementById('threejs-container');
    if (!container) return;
    
    // Hide loading text
    const loadingText = document.getElementById('threejs-loading');
    if (loadingText) loadingText.style.display = 'none';

    const width = container.clientWidth;
    const height = container.clientHeight;

    const scene = new THREE.Scene();
    
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = 5;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);

    // Premium AI Core 3D Visualization
    const geometry = new THREE.IcosahedronGeometry(2, 1);
    const material = new THREE.MeshStandardMaterial({ 
        color: 0x8b5cf6, 
        wireframe: true,
        emissive: 0x4c1d95,
        emissiveIntensity: 0.5
    });
    const core = new THREE.Mesh(geometry, material);
    scene.add(core);

    // Particle Ring
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 300;
    const posArray = new Float32Array(particlesCount * 3);
    for(let i = 0; i < particlesCount * 3; i++) {
        posArray[i] = (Math.random() - 0.5) * 8;
    }
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const particlesMaterial = new THREE.PointsMaterial({
        size: 0.05,
        color: 0x0ea5e9,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending
    });
    const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particlesMesh);

    // Lighting
    const pointLight = new THREE.PointLight(0xffffff, 1);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);

    let time = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.01;
        
        core.rotation.x += 0.005;
        core.rotation.y += 0.01;
        
        // Pulsate core
        const scale = 1 + Math.sin(time * 2) * 0.05;
        core.scale.set(scale, scale, scale);

        particlesMesh.rotation.y -= 0.002;
        particlesMesh.rotation.x += 0.001;
        
        renderer.render(scene, camera);
    }
    animate();

    // Handle resize
    window.addEventListener('resize', () => {
        if (!container) return;
        const newWidth = container.clientWidth;
        const newHeight = container.clientHeight;
        renderer.setSize(newWidth, newHeight);
        camera.aspect = newWidth / newHeight;
        camera.updateProjectionMatrix();
    });
}

// Call initThreeJS when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initThreeJS();
});
