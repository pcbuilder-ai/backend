package com.example.pcproject.service;

import com.example.pcproject.domain.Estimate;
import com.example.pcproject.repository.EstimateRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class EstimateService {

    private final EstimateRepository estimateRepository;
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
                .build();

        estimateRepository.save(estimate);
        System.out.println("💾 DB에 견적 저장 완료 (user_id=" + userId + ")");
    }

    // ✅ 사용자별 견적 조회
    public List<Estimate> getEstimatesByUser(Long userId) {
        return estimateRepository.findByUserId(userId);
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
