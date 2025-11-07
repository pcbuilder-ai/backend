package com.example.pcproject.repository;

import com.example.pcproject.domain.Estimate;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface EstimateRepository extends JpaRepository<Estimate, Long> {
    List<Estimate> findByUserId(Long userId);
}
