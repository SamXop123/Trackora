"use client";

import React, { useEffect, useRef } from "react";

interface Star {
  x: number;
  y: number;
  size: number;
  speedX: number;
  speedY: number;
  opacity: number;
  targetOpacity: number;
}

interface StarfieldProps {
  warpActive?: boolean;
}

export default function Starfield({ warpActive = false }: StarfieldProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: 0, y: 0, active: false });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let stars: Star[] = [];
    const count = 120;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      initStars();
    };

    const initStars = () => {
      stars = [];
      for (let i = 0; i < count; i++) {
        stars.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          size: Math.random() * 1.5 + 0.5,
          speedX: (Math.random() - 0.5) * 0.08,
          speedY: (Math.random() - 0.5) * 0.08,
          opacity: Math.random(),
          targetOpacity: Math.random() * 0.8 + 0.2,
        });
      }
    };

    let mouseVelocity = 0;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      mouseVelocity *= 0.9; // decay velocity

      stars.forEach((star) => {
        // Drift movement
        const speedMultiplier = warpActive ? 45 : 1;
        star.x += star.speedX * speedMultiplier;
        star.y += star.speedY * speedMultiplier;

        // Wrap around screen edges
        if (star.x < 0) star.x = canvas.width;
        if (star.x > canvas.width) star.x = 0;
        if (star.y < 0) star.y = canvas.height;
        if (star.y > canvas.height) star.y = 0;

        // Smooth opacity pulsing
        star.opacity += (star.targetOpacity - star.opacity) * 0.02;
        if (Math.abs(star.opacity - star.targetOpacity) < 0.05) {
          star.targetOpacity = Math.random() * 0.8 + 0.2;
        }

        // Mouse attraction warp
        let forceX = 0;
        let forceY = 0;
        if (mouseRef.current.active) {
          const dx = mouseRef.current.x - star.x;
          const dy = mouseRef.current.y - star.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 180) {
            const force = (180 - dist) / 180;
            // Pull stars slightly towards mouse cursor
            forceX = dx * force * 0.015;
            forceY = dy * force * 0.015;
            star.x += forceX;
            star.y += forceY;
          }
        }

        // Draw star with velocity stretch or circular orbit drift
        ctx.beginPath();
        if (warpActive || mouseVelocity > 3) {
          const lengthFactor = warpActive ? 0.8 : 0.25;
          const vx = (star.speedX * (warpActive ? 45 : 1)) + (forceX * mouseVelocity * lengthFactor);
          const vy = (star.speedY * (warpActive ? 45 : 1)) + (forceY * mouseVelocity * lengthFactor);
          ctx.moveTo(star.x, star.y);
          ctx.lineTo(star.x - vx * 4, star.y - vy * 4);
          ctx.strokeStyle = `rgba(248, 250, 252, ${star.opacity * 0.9})`;
          ctx.lineWidth = star.size * (warpActive ? 0.7 : 0.9);
          ctx.stroke();
        } else {
          ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(248, 250, 252, ${star.opacity})`;
          ctx.fill();
        }
      });

      animationFrameId = requestAnimationFrame(draw);
    };

    const handleMouseMove = (e: MouseEvent) => {
      const dx = e.clientX - mouseRef.current.x;
      const dy = e.clientY - mouseRef.current.y;
      const vel = Math.sqrt(dx * dx + dy * dy);
      mouseVelocity = Math.min(vel, 35); // Cap velocity impact
      mouseRef.current.x = e.clientX;
      mouseRef.current.y = e.clientY;
      mouseRef.current.active = true;
    };

    const handleMouseLeave = () => {
      mouseRef.current.active = false;
      mouseVelocity = 0;
    };

    window.addEventListener("resize", resizeCanvas);
    window.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseleave", handleMouseLeave);

    resizeCanvas();
    draw();

    return () => {
      window.removeEventListener("resize", resizeCanvas);
      window.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseleave", handleMouseLeave);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        zIndex: 0,
        pointerEvents: "none",
        background: "radial-gradient(circle at 50% 50%, #080c14 0%, #04060a 100%)",
      }}
    />
  );
}
