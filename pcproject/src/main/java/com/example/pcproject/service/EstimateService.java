package com.example.pcproject.service;

import com.example.pcproject.domain.Estimate;
import com.example.pcproject.domain.User;
import com.example.pcproject.repository.EstimateRepository;
import com.example.pcproject.repository.UserRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class EstimateService {

    private final EstimateRepository estimateRepository;
    private final UserRepository userRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    // ✅ 견적 저장
    public void saveEstimate(Long userId, Map<String, Object> estimateData) throws Exception {
        String title = (String) estimateData.getOrDefault("title", "AI 추천 견적");
        Integer totalPrice = (Integer) estimateData.getOrDefault("totalPrice", 0);

        // 전체 데이터를 JSON으로 직렬화
        String jsonData = objectMapper.writeValueAsString(estimateData);

        Estimate estimate = Estimate.builder()
                .userId(userId)
                .title(title)
                .totalPrice(totalPrice)
                .data(jsonData)
                .createdAt(LocalDateTime.now())
                .build();

        estimateRepository.save(estimate);
        System.out.println("💾 [DEBUG] Estimate 저장 직전 ----------------------------");
        System.out.println("   userId     = " + estimate.getUserId());
        System.out.println("   title      = " + estimate.getTitle());
        System.out.println("   totalPrice = " + estimate.getTotalPrice());
        System.out.println("   data len   = " + (estimate.getData() != null ? estimate.getData().length() : "null"));
        System.out.println("----------------------------------------------------------");
        System.out.println("💾 DB에 견적 저장 완료 (user_id=" + userId + ")");
    }

    // ✅ 사용자별 견적 조회
    public List<Estimate> getEstimatesByUser(Long userId) {
        return estimateRepository.findByUserId(userId);
    }

    // ✅ 모든 견적 조회 (갤러리용)
    public List<Map<String, Object>> getAllEstimates() {
        List<Estimate> estimates = estimateRepository.findAll();
        
        return estimates.stream().map(estimate -> {
            Map<String, Object> result = new HashMap<>();
            result.put("id", estimate.getId());
            result.put("title", estimate.getTitle());
            result.put("totalPrice", estimate.getTotalPrice());
            result.put("data", estimate.getData());
            result.put("createdAt", estimate.getCreatedAt());
            
            // 사용자 정보 추가
            Optional<User> userOpt = userRepository.findById(estimate.getUserId());
            if (userOpt.isPresent()) {
                User user = userOpt.get();
                result.put("username", user.getName()); // 사용자 이름
                result.put("userId", user.getId());
            } else {
                result.put("username", "알 수 없음");
            }
            
            return result;
        }).collect(Collectors.toList());
    }

    // ✅ 견적 삭제
    public boolean deleteEstimate(Long id, Long userId) {
        Optional<Estimate> estimateOpt = estimateRepository.findById(id);
        if (estimateOpt.isEmpty()) return false;

        Estimate estimate = estimateOpt.get();
        if (!estimate.getUserId().equals(userId)) {
            // 다른 사람 견적은 삭제 불가
            return false;
        }

        estimateRepository.delete(estimate);
        return true;
    }
}
