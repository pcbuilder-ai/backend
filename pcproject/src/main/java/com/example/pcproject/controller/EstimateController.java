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
        System.out.println("🔥 [saveEstimate] userId = " + userId);

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

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteEstimate(@PathVariable Long id, HttpSession session) {
        Long userId = (Long) session.getAttribute("user_id");

        if (userId == null) {
            return ResponseEntity.status(401).body(Map.of(
                    "success", false,
                    "message", "로그인이 필요합니다."
            ));
        }

        boolean deleted = estimateService.deleteEstimate(id, userId);

        if (deleted) {
            return ResponseEntity.ok(Map.of(
                    "success", true,
                    "message", "견적이 삭제되었습니다."
            ));
        } else {
            return ResponseEntity.status(403).body(Map.of(
                    "success", false,
                    "message", "삭제 권한이 없거나 견적이 존재하지 않습니다."
            ));
        }
    }
}
