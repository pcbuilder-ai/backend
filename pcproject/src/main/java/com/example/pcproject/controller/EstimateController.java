package com.example.pcproject.controller;

import com.example.pcproject.service.EstimateService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.HttpSession;
import java.util.Map;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/estimate")
public class EstimateController {

    private final EstimateService estimateService;

    @PostMapping("/save")
    public ResponseEntity<?> saveEstimate(@RequestBody Map<String, Object> req, HttpSession session) {
        Long userId = (Long) session.getAttribute("user_id");

        if (userId == null) {
            return ResponseEntity.status(401).body(Map.of(
                    "success", false,
                    "message", "로그인이 필요합니다."
            ));
        }

        try {
            estimateService.saveEstimate(userId, req);
            return ResponseEntity.ok(Map.of(
                    "success", true,
                    "message", "견적이 저장되었습니다."
            ));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "message", e.getMessage()
            ));
        }
    }

    @GetMapping("/list")
    public ResponseEntity<?> listEstimates(HttpSession session) {
        Long userId = (Long) session.getAttribute("user_id");

        if (userId == null) {
            return ResponseEntity.status(401).body(Map.of(
                    "success", false,
                    "message", "로그인이 필요합니다."
            ));
        }

        return ResponseEntity.ok(Map.of(
                "success", true,
                "estimates", estimateService.getEstimatesByUser(userId)
        ));
    }
}
