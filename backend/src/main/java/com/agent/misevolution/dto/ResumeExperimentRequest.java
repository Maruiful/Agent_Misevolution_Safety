package com.agent.misevolution.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 恢复实验请求
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ResumeExperimentRequest {

    /**
     * 实验 UUID
     */
    private String experimentUuid;
}
